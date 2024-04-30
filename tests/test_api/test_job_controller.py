"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""
import json
import time

from diablo import std_commit
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.house_keeping_job import HouseKeepingJob
from diablo.models.job import Job
from diablo.models.job_history import JobHistory
from flask import current_app as app
import pytest
from tests.util import scheduled_job, simply_yield

admin_uid = '90001'
instructor_uid = '10001'


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login(admin_uid)


@pytest.fixture()
def instructor_session(fake_auth):
    fake_auth.login(instructor_uid)


class TestStartJob:

    @staticmethod
    def _api_start_job(client, job_key, expected_status_code=200):
        response = client.get(f'/api/job/{job_key}/start')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_start_job(client, job_key='emails', expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_start_job(client, job_key='emails', expected_status_code=401)

    def test_job_not_found(self, client, admin_session):
        """404 if job key is unrecognized."""
        self._api_start_job(client, job_key='space_for_rent', expected_status_code=404)

    def test_authorized(self, client, admin_session):
        """Admin can start a job."""
        job_key = 'canvas'
        self._api_start_job(client, job_key=job_key)
        # Now verify
        response = client.get('/api/job/history')
        assert response.status_code == 200
        job_history = response.json
        assert len(job_history)
        assert job_history[0]['jobKey'] == job_key
        assert job_history[0]['failed'] is False
        assert job_history[0]['startedAt']
        assert 'finishedAt' in job_history[0]

    def test_force_run_of_disabled_job(self, client, admin_session):
        """Disabled job will run if run on-demand."""
        job_key = 'blackouts'
        self._api_start_job(client, job_key=job_key)
        time.sleep(0.7)
        # Now verify
        response = client.get('/api/job/history')
        assert response.status_code == 200
        job_history = response.json
        assert len(job_history)
        assert job_key in [h['jobKey'] for h in job_history]


class TestJobHistory:

    @staticmethod
    def _api_job_history(client, expected_status_code=200):
        response = client.get('/api/job/history')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_job_history(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_job_history(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin can access job_history."""
        CanvasJob(simply_yield).run()
        CanvasJob(simply_yield).run()

        job_history = self._api_job_history(client)
        assert len(job_history) > 1
        for event in job_history:
            assert event['failed'] is False
            assert event['startedAt']
            assert 'finishedAt' in event


class TestDisableJob:

    @staticmethod
    def _api_job_disable(client, job_id, disable, expected_status_code=200):
        response = client.post(
            '/api/job/disable',
            data=json.dumps({
                'jobId': job_id,
                'disable': disable,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_job_disable(client, job_id=1, disable=True, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_job_disable(client, job_id=1, disable=True, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin can access available jobs."""
        with scheduled_job('blackouts') as job:
            expected_value = not job.disabled
            api_json = self._api_job_disable(client, job_id=job.id, disable=expected_value)
            assert api_json['disabled'] is expected_value
            std_commit(allow_test_environment=True)

            # Reset the value
            expected_value = not expected_value
            api_json = self._api_job_disable(client, job_id=job.id, disable=expected_value)
            assert api_json['disabled'] is expected_value
            std_commit(allow_test_environment=True)


class TestUpdateJobSchedule:

    @staticmethod
    def _api_job_update_schedule(client, job_id, schedule_type, schedule_value, expected_status_code=200):
        response = client.post(
            '/api/job/schedule/update',
            data=json.dumps({
                'jobId': job_id,
                'type': schedule_type,
                'value': schedule_value,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_job_update_schedule(
            client,
            job_id=1,
            schedule_type='minutes',
            schedule_value=3,
            expected_status_code=401,
        )

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_job_update_schedule(
            client,
            job_id=1,
            schedule_type='minutes',
            schedule_value=3,
            expected_status_code=401,
        )

    def test_invalid_schedule_type(self, client, instructor_session):
        """Error when invalid schedule_type."""
        self._api_job_update_schedule(
            client,
            job_id=1,
            schedule_type='this_is_not_a_type',
            schedule_value=3,
            expected_status_code=401,
        )

    def test_invalid_schedule_value(self, client, instructor_session):
        """Error when invalid schedule_value."""
        self._api_job_update_schedule(
            client,
            job_id=1,
            schedule_type='minutes',
            schedule_value=-30,
            expected_status_code=401,
        )

    def test_edit_schedule_of_enabled_job(self, client, admin_session):
        """You cannot edit job schedule if the job is enabled."""
        with scheduled_job(job_key=CanvasJob.key()) as job:
            Job.update_disabled(job_id=job.id, disable=False)
            std_commit(allow_test_environment=True)
            self._api_job_update_schedule(
                client,
                expected_status_code=400,
                job_id=Job.get_job_by_key('canvas').id,
                schedule_type='minutes',
                schedule_value=3,
            )

    def test_edit_schedule_of_running_job(self, client, admin_session):
        """You cannot edit job schedule if the job is running."""
        with scheduled_job('blackouts') as job:
            job_history = JobHistory.job_started(job_key=job.key)
            self._api_job_update_schedule(
                client,
                expected_status_code=400,
                job_id=job.id,
                schedule_type='minutes',
                schedule_value=3,
            )
            JobHistory.job_finished(id_=job_history.id, failed=False)

    def test_authorized(self, client, admin_session):
        """Admin can edit job schedule."""
        with scheduled_job('blackouts') as job:
            # Job must be disabled in order to update schedule
            Job.update_disabled(job_id=job.id, disable=True)
            api_json = self._api_job_update_schedule(
                client,
                job_id=job.id,
                schedule_type='minutes',
                schedule_value=3,
            )
            assert api_json['schedule'] == {
                'type': 'minutes',
                'value': 3,
            }
            api_json = self._api_job_update_schedule(
                client,
                job_id=job.id,
                schedule_type='day_at',
                schedule_value='15:30',
            )
            assert api_json['schedule'] == {
                'type': 'day_at',
                'value': '15:30',
            }


class TestJobSchedule:

    @staticmethod
    def _api_job_schedule(client, expected_status_code=200):
        response = client.get('/api/job/schedule')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_job_schedule(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_job_schedule(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin can access job_history."""
        api_json = self._api_job_schedule(client)
        assert api_json['autoStart'] is app.config['JOBS_AUTO_START']
        assert api_json['secondsBetweenJobsCheck'] == app.config['JOBS_SECONDS_BETWEEN_PENDING_CHECK']
        first_job = api_json['jobs'][0]
        assert first_job['key'] == 'blackouts'
        assert first_job['name'] == 'Blackouts'
        assert first_job['disabled'] is True
        assert first_job['schedule'] == {
            'type': 'minutes',
            'value': 120,
        }
        kaltura_job = api_json['jobs'][-3]
        assert kaltura_job['key'] == 'kaltura'
        assert kaltura_job['disabled'] is False
        assert kaltura_job['schedule'] == {
            'type': 'day_at',
            'value': '15:00',
        }


class TestLastSuccessfulRun:

    @staticmethod
    def _api_last_successful_run(client, job_key, expected_status_code=200):
        response = client.get(f'/api/job/{job_key}/last_successful_run')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_last_successful_run(client, job_key='house_keeping', expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_last_successful_run(client, job_key='house_keeping', expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin can access job_history."""
        job_key = 'house_keeping'
        api_json = self._api_last_successful_run(client, job_key=job_key)
        assert api_json['jobKey'] == job_key
        finished_at = api_json['finishedAt']
        assert finished_at

        HouseKeepingJob(app_context=simply_yield).run()
        assert self._api_last_successful_run(client, job_key=job_key)['finishedAt'] > finished_at
