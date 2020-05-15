"""
Copyright ©2020. The Regents of the University of California (Regents). All Rights Reserved.

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
from flask import current_app as app
import pytest

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
        self._api_start_job(client, job_key='queued_emails_job', expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_start_job(client, job_key='queued_emails_job', expected_status_code=401)

    def test_job_not_found(self, client, admin_session):
        """404 if job key is unrecognized."""
        self._api_start_job(client, job_key='space_for_rent', expected_status_code=404)

    def test_authorized(self, client, admin_session):
        """Admin can start a job."""
        job_key = 'queued_emails'
        self._api_start_job(client, job_key=job_key)
        # Now verify
        response = client.get('/api/job/history/1')
        assert response.status_code == 200
        job_history = response.json
        assert len(job_history)
        assert job_history[0]['jobKey'] == job_key
        assert job_history[0]['failed'] is False
        assert job_history[0]['startedAt']
        assert 'finishedAt' in job_history[0]


class TestJobHistory:

    @staticmethod
    def _api_job_history(client, day_count, expected_status_code=200):
        response = client.get(f'/api/job/history/{day_count}')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_job_history(client, day_count=1, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_job_history(client, day_count=1, expected_status_code=401)

    def test_invalid_arg(self, client, admin_session):
        """Complains when invalid day_count arg."""
        self._api_job_history(client, day_count=0, expected_status_code=400)
        self._api_job_history(client, day_count=-2, expected_status_code=400)
        self._api_job_history(client, day_count='foo', expected_status_code=400)

    def test_authorized(self, client, admin_session):
        """Admin can access job_history."""
        job_history = self._api_job_history(client, day_count=2)
        assert len(job_history) > 1
        for event in job_history:
            assert event['failed'] is False
            assert event['startedAt']
            assert event['finishedAt']


class TestJobsAvailable:

    @staticmethod
    def _api_jobs_available(client, expected_status_code=200):
        response = client.get('/api/jobs/available')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_jobs_available(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_jobs_available(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin can access available jobs."""
        available_jobs = self._api_jobs_available(client)
        assert len(available_jobs) > 1
        for available_job in available_jobs:
            assert available_job['key']
            assert len(available_job['description'])


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
        assert first_job['key'] == 'admin_emails'
        assert first_job['name'] == 'AdminEmailsJob'
        assert first_job['disabled'] is True
        assert first_job['schedule'] == {
            'type': 'seconds',
            'value': 1,
        }

        last_job = api_json['jobs'][-1]
        assert last_job['key'] == 'queued_emails'
        assert last_job['disabled'] is False
        assert last_job['schedule'] == {
            'type': 'day_at',
            'value': '04:30',
        }
