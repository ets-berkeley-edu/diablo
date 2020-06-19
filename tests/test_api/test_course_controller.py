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
import csv
from io import StringIO
import json
import random

from diablo import std_commit
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.models.approval import Approval
from diablo.models.course_preference import CoursePreference
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
import pytest
from tests.test_api.api_test_utils import api_approve, api_get_course, get_instructor_uids, get_meeting_data
from tests.util import simply_yield, test_approvals_workflow

admin_uid = '90001'
deleted_admin_user_uid = '910001'
section_1_id = 50000
section_2_id = 50001
section_3_id = 50002
section_4_id = 50004
section_5_id = 50003
section_6_id = 50005
section_7_id = 50010

section_in_ineligible_room = section_2_id
section_with_canvas_course_sites = section_6_id


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login(admin_uid)


class TestApprove:
    """Only admins and authorized instructors can sign a course up for Course Capture."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        api_approve(
            client,
            publish_type='kaltura_my_media',
            recording_type='presentation_audio',
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_invalid_publish_type(self, client, admin_session):
        """Reject invalid publish types."""
        api_approve(
            client,
            publish_type='youtube',
            recording_type='presentation_audio',
            section_id=section_1_id,
            expected_status_code=400,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny access if the instructor is not teaching the requested course."""
        fake_auth.login('10006')
        api_approve(
            client,
            publish_type='kaltura_my_media',
            recording_type='presentation_audio',
            section_id=section_2_id,
            expected_status_code=403,
        )

    def test_instructor_already_approved(self, client, fake_auth):
        """Instructor can submit his/her approval only once."""
        with test_approvals_workflow(app):
            instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            fake_auth.login(instructor_uids[0])

            for expected_status_code in [200, 403]:
                api_approve(
                    client,
                    publish_type='kaltura_my_media',
                    recording_type='presentation_audio',
                    section_id=section_1_id,
                    expected_status_code=expected_status_code,
                )

    def test_approval_by_instructors(self, app, client, fake_auth):
        """Instructor can submit approval if s/he is teaching the requested course."""
        with test_approvals_workflow(app):
            instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            fake_auth.login(instructor_uids[0])
            api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presentation_audio',
                section_id=section_1_id,
            )
            std_commit(allow_test_environment=True)

            fake_auth.login(instructor_uids[1])
            api_approve(
                client,
                publish_type='kaltura_media_gallery',
                recording_type='presentation_audio',
                section_id=section_1_id,
            )
            std_commit(allow_test_environment=True)

            QueuedEmailsJob(app.app_context).run()

            # First instructor was notified 1) that second instructor needed to approve; 2) that second instructor made changes.
            emails_sent = SentEmail.get_emails_sent_to(instructor_uids[0])
            assert len(emails_sent) == 2
            for email in emails_sent:
                assert email.section_id == section_1_id
                assert email.term_id == self.term_id
            assert emails_sent[0].template_type == 'waiting_for_approval'
            assert emails_sent[1].template_type == 'notify_instructor_of_changes'

            # Second instructor received no notifications.
            assert len(SentEmail.get_emails_sent_to(instructor_uids[1])) == 0

            fake_auth.login(admin_uid)
            api_json = api_get_course(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
            )
            assert api_json['meetings'][0]['room']['location'] == 'Barrows 106'
            instructor_uids = [i['uid'] for i in api_json['instructors']]
            assert instructor_uids == instructor_uids
            approvals_ = api_json['approvals']
            assert len(approvals_) == 2

            assert approvals_[0]['approvedBy']['uid'] == instructor_uids[0]
            assert approvals_[0]['publishType'] == 'kaltura_my_media'

            assert approvals_[1]['approvedBy']['uid'] == instructor_uids[1]
            assert approvals_[1]['publishType'] == 'kaltura_media_gallery'
            assert approvals_[1]['recordingType'] == 'presentation_audio'
            assert approvals_[1]['recordingTypeName'] == 'Presentation and Audio'

            assert api_json['hasNecessaryApprovals'] is True
            assert api_json['scheduled'] is None

    def test_approval_by_admin(self, client, admin_session):
        """Admins can schedule recordings on behalf of any eligible course."""
        with test_approvals_workflow(app):
            api_json = api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presentation_audio',
                section_id=section_1_id,
            )
            std_commit(allow_test_environment=True)
            assert api_json['hasNecessaryApprovals'] is True
            assert api_json['scheduled'] is None

    def test_has_necessary_approvals_when_cross_listed(self, client, fake_auth):
        """If section X and Y are cross-listed then hasNecessaryApprovals is false until the Y instructor approves."""
        with test_approvals_workflow(app):
            def _approve(instructor_uid, expected_has_necessary):
                fake_auth.login(instructor_uid)
                api_json = api_approve(
                    client,
                    publish_type='kaltura_my_media',
                    recording_type='presentation_audio',
                    section_id=50012,
                )
                std_commit(allow_test_environment=True)
                assert api_json['hasNecessaryApprovals'] is expected_has_necessary, f'instructor_uid: {instructor_uid}'

            _approve(instructor_uid='10009', expected_has_necessary=False)
            # Log out
            client.get('/api/auth/logout')
            _approve(instructor_uid='10010', expected_has_necessary=True)


class TestGetCourse:
    """Course can be viewed by its instructors and Diablo admin users."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        """Deny access if user is not an admin."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_3_id,
            expected_status_code=403,
        )

    def test_deny_deleted_admin_user(self, client, fake_auth):
        """Deny access if admin user was deleted."""
        fake_auth.login(deleted_admin_user_uid)
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_invalid_section_id(self, client, admin_session):
        """404 if section does not exist."""
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=999999,
            expected_status_code=404,
        )

    def test_course_with_partial_approval(self, client, admin_session):
        """Course with two instructors and one approval."""
        with test_approvals_workflow(app):
            # If course has approvals but not scheduled then it will show up in the feed.
            approved_by_uid = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)[0]
            room_id = Room.get_room_id(section_id=section_1_id, term_id=self.term_id)
            Approval.create(
                approved_by_uid=approved_by_uid,
                approver_type_='instructor',
                publish_type_='kaltura_my_media',
                recording_type_='presentation_audio',
                room_id=room_id,
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)

            api_json = api_get_course(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
            )
            assert [i['uid'] for i in api_json['instructors']] == ['10001', '10002']

            approvals = api_json['approvals']
            assert len(approvals) == 1
            assert approved_by_uid == approvals[0]['approvedBy']['uid']
            assert api_json['approvalStatus'] == 'Partially Approved'
            assert api_json['schedulingStatus'] == 'Not Scheduled'
            assert api_json['meetings'][0]['room']['id'] == room_id
            assert api_json['meetings'][0]['room']['location'] == 'Barrows 106'

    def test_date_time_format(self, client, fake_auth):
        """Dates and times are properly formatted for front-end display."""
        instructor_uids = get_instructor_uids(section_id=section_2_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert api_json['meetings'][0]['daysFormatted'] == ['MO', 'WE', 'FR']
        assert api_json['meetings'][0]['startTimeFormatted'] == '3:00 pm'
        assert api_json['meetings'][0]['endTimeFormatted'] == '3:59 pm'
        assert api_json['meetings'][0]['location'] == 'Wheeler 150'

    def test_li_ka_shing_recording_options(self, client, admin_session):
        """Rooms designated as 'auditorium' offer ALL types of recording."""
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_3_id,
        )
        assert api_json['meetings'][0]['room']['location'] == 'Li Ka Shing 145'
        assert len(api_json['meetings'][0]['room']['recordingTypeOptions']) == 3

    def test_section_with_canvas_course_sites(self, client, admin_session):
        """Canvas course site information is included in the API."""
        CanvasJob(simply_yield).run()
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_with_canvas_course_sites,
        )
        assert len(api_json['canvasCourseSites']) == 3

    def test_cross_listing(self, client, fake_auth):
        """Course has cross-listings."""
        section_id = 50007
        cross_listed_section_ids = {50008, 50009}
        instructor_uid = '10008'
        fake_auth.login(uid=instructor_uid)

        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_id,
        )
        assert cross_listed_section_ids == set([c['sectionId'] for c in api_json['crossListings']])
        # Verify that cross-listed section_ids have been "deleted" in sis_sections table
        for section_id_ in cross_listed_section_ids:
            api_get_course(
                client,
                term_id=self.term_id,
                section_id=section_id_,
                expected_status_code=404,
            )

    def test_instructor_of_cross_listing(self, client, fake_auth):
        """If section X and Y are cross-listed then /course page of X must be reachable by instructor of Y."""
        section_id = 50012
        cross_listed_section_id = 50013
        instructor_uid = '10010'
        # Confirm that cross-listed section was deleted during sis_data_refresh job
        assert not SisSection.get_course(section_id=cross_listed_section_id, term_id=self.term_id)
        # Log in as instructor of cross-listed section
        fake_auth.login(uid=instructor_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_id,
        )
        assert len(api_json['crossListings']) == 1
        assert cross_listed_section_id == api_json['crossListings'][0]['sectionId']
        assert instructor_uid in [i['uid'] for i in api_json['instructors']]

    def test_no_cross_listing(self, client, admin_session):
        """Course does not have cross-listing."""
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert len(api_json['crossListings']) == 0


class TestGetCourses:
    """Only admins can see who has been invited, who has signed up, etc."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_courses(client, term_id, filter_=None, expected_status_code=200):
        response = client.post(
            '/api/courses',
            data=json.dumps({
                'termId': term_id,
                'filter': filter_ or 'Not Invited',
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def _send_invitation_email(self, section_id):
        SentEmail.create(
            section_id=section_id,
            recipient_uid=get_instructor_uids(section_id=section_id, term_id=self.term_id)[0],
            template_type='invitation',
            term_id=self.term_id,
        )

    def _create_approval(self, section_id):
        Approval.create(
            approved_by_uid=get_instructor_uids(section_id=section_id, term_id=self.term_id)[0],
            approver_type_='instructor',
            publish_type_='kaltura_my_media',
            recording_type_='presentation_audio',
            room_id=Room.get_room_id(section_id=section_id, term_id=self.term_id),
            section_id=section_id,
            term_id=self.term_id,
        )

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_do_not_email_filter(self, client, admin_session):
        """Do Not Email filter: Courses in eligible room; "opt out" is true; all stages of approval; not scheduled."""
        with test_approvals_workflow(app):
            # Send invites them opt_out.
            for section_id in (section_1_id, section_in_ineligible_room, section_3_id, section_4_id):
                CoursePreference.update_opt_out(section_id=section_id, term_id=self.term_id, opt_out=True)

                in_enabled_room = _is_course_in_enabled_room(section_id=section_id, term_id=self.term_id)
                if section_id == section_in_ineligible_room:
                    # Courses in ineligible rooms will be excluded from the feed.
                    assert not in_enabled_room
                else:
                    assert in_enabled_room
                    self._send_invitation_email(section_id)

            # If course has approvals but not scheduled then it will show up in the feed.
            self._create_approval(section_4_id)
            # Feed will exclude scheduled.
            _schedule_recordings(
                section_id=section_3_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)

            api_json = self._api_courses(client, term_id=self.term_id, filter_='Do Not Email')

            # Opted-out courses are in the feed, whether approved or not
            course_1 = _find_course(api_json=api_json, section_id=section_1_id)
            assert course_1['approvalStatus'] == 'Invited'
            assert course_1['schedulingStatus'] == 'Not Scheduled'
            course_4 = _find_course(api_json=api_json, section_id=section_4_id)
            assert course_4['approvalStatus'] == 'Approved'
            assert course_4['schedulingStatus'] == 'Queued for Scheduling'

            for section_id in (section_3_id, section_in_ineligible_room):
                # Excluded courses
                assert not _find_course(api_json=api_json, section_id=section_id)

    def test_invited_filter(self, client, admin_session):
        """Invited filter: Course in an eligible room, have received invitation. No approvals. Not scheduled."""
        with test_approvals_workflow(app):
            # First, send invitations
            self._send_invitation_email(section_4_id)
            self._send_invitation_email(section_5_id)
            # The section with approval will NOT show up in search results
            self._create_approval(section_5_id)

            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Invited')
            # Section with ZERO approvals will show up in search results
            course = _find_course(api_json=api_json, section_id=section_4_id)
            assert course
            assert course['label'] == 'CHEM C110L, LAB 001'
            assert course['approvalStatus'] == 'Invited'
            assert course['schedulingStatus'] == 'Not Scheduled'
            # The section with approval will NOT show up in search results
            assert not _find_course(api_json=api_json, section_id=section_5_id)

    def test_not_invited_filter(self, client, admin_session):
        """Not-invited filter: Courses in eligible rooms, never sent an invitation. No approval. Not scheduled."""
        with test_approvals_workflow(app):
            # The first course gets an invitation
            self._send_invitation_email(section_1_id)

            # The second course did not receive an invitation BUT it does have approval.
            invite = SentEmail.get_emails_of_type(
                section_ids=[section_4_id],
                template_type='invitation',
                term_id=self.term_id,
            )
            assert not invite

            self._create_approval(section_4_id)
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Not Invited')
            assert not _find_course(api_json=api_json, section_id=section_1_id)
            assert not _find_course(api_json=api_json, section_id=section_4_id)
            # Third course is in enabled room and has not received an invite. Therefore, it is in the feed.
            assert _is_course_in_enabled_room(section_id=section_3_id, term_id=self.term_id)
            course = _find_course(api_json=api_json, section_id=section_3_id)
            assert course['approvalStatus'] == 'Not Invited'
            assert course['schedulingStatus'] == 'Not Scheduled'
            assert course['label'] == 'BIO 1B, LEC 001'

    def test_partially_approved_filter(self, client, admin_session):
        """Partially approved: Eligible, invited course with 1+ approvals, but not ALL instructors have approved."""
        with test_approvals_workflow(app):
            for section_id in [section_1_id, section_6_id, section_7_id]:
                # Assert multiple instructors
                assert len(get_instructor_uids(section_id=section_id, term_id=self.term_id)) > 1
                # Send invites
                self._send_invitation_email(section_id)
                if section_id == section_1_id:
                    # If course is "approved" by admin only then it will NOT show up on the partially-approval list.
                    Approval.create(
                        approved_by_uid=admin_uid,
                        approver_type_='admin',
                        publish_type_='kaltura_my_media',
                        recording_type_='presentation_audio',
                        room_id=Room.get_room_id(section_id=section_id, term_id=self.term_id),
                        section_id=section_id,
                        term_id=self.term_id,
                    )
                else:
                    # Approval by first instructor only
                    self._create_approval(section_id)

            # Feed will include both scheduled and not scheduled.
            for section_id in [section_1_id, section_7_id]:
                _schedule_recordings(section_id=section_id, term_id=self.term_id)

            # Unschedule one of them
            Approval.delete(section_id=section_7_id, term_id=self.term_id)
            Scheduled.delete(section_id=section_7_id, term_id=self.term_id)

            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Partially Approved')
            assert len(api_json) == 1
            course = _find_course(api_json=api_json, section_id=section_6_id)
            assert course
            assert course['label'] == 'LAW 23, LEC 002'
            assert course['approvalStatus'] == 'Partially Approved'
            assert course['schedulingStatus'] == 'Not Scheduled'

    def test_scheduled_filter(self, client, admin_session):
        """Scheduled filter: Courses with recordings scheduled."""
        with test_approvals_workflow(app):
            # Send invites
            for section_id in [section_1_id, section_6_id]:
                self._send_invitation_email(section_id)
                self._create_approval(section_id)

            # Feed will only include courses that were scheduled.
            _schedule_recordings(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            # Deleted records will be ignored
            _schedule_recordings(
                section_id=section_2_id,
                term_id=self.term_id,
            )
            Scheduled.delete(section_id=section_2_id, term_id=self.term_id)
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Scheduled')
            assert len(api_json) == 1
            course = _find_course(api_json=api_json, section_id=section_1_id)
            assert course['approvalStatus'] == 'Partially Approved'
            assert course['schedulingStatus'] == 'Scheduled'
            assert not _find_course(api_json=api_json, section_id=section_6_id)

    def test_all_filter(self, client, admin_session):
        """The 'all' filter returns all courses in eligible rooms."""
        with test_approvals_workflow(app):
            # Put courses in a few different states.
            for section_id in [section_1_id, section_6_id]:
                self._send_invitation_email(section_id)
                self._create_approval(section_id)
            _schedule_recordings(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            # We gotta catch 'em all.
            api_json = self._api_courses(client, term_id=self.term_id, filter_='All')
            assert len(api_json) == 8
            for section_id in [section_1_id, section_3_id, section_4_id, section_5_id, section_6_id]:
                assert _find_course(api_json=api_json, section_id=section_id)
            assert not _find_course(api_json=api_json, section_id=section_in_ineligible_room)


class TestDownloadCoursesCsv:
    """Only admins download courses CSV."""

    @staticmethod
    def _api_courses_csv(client, expected_status_code=200):
        response = client.post(
            '/api/courses/csv',
            data=json.dumps({
                'termId': app.config['CURRENT_TERM_ID'],
                'filter': 'All',
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.data

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses_csv(client, expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        """Deny access if user is not an admin."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=app.config['CURRENT_TERM_ID'])
        fake_auth.login(instructor_uids[0])
        self._api_courses_csv(client, expected_status_code=401)

    def test_download_csv(self, client, admin_session):
        """Admin users can download courses CSV file."""
        term_id = app.config['CURRENT_TERM_ID']
        csv_string = self._api_courses_csv(client).decode('utf-8')
        reader = csv.reader(StringIO(csv_string), delimiter=',')
        for index, row in enumerate(reader):
            section_id = row[1]
            sign_up_url = row[8]
            instructors = row[-2]
            instructor_uids = row[-1]
            if index == 0:
                assert section_id == 'Section Id'
                assert sign_up_url == 'Sign-up URL'
                assert instructors == 'Instructors'
                assert instructor_uids == 'Instructor UIDs'
            else:
                course = SisSection.get_course(section_id=section_id, term_id=term_id)
                assert int(section_id) == course['sectionId']
                for snippet in [app.config['DIABLO_BASE_URL'], section_id, str(term_id)]:
                    assert snippet in sign_up_url

                expected_uids = [instructor['uid'] for instructor in course['instructors']]
                assert set(instructor_uids.split(', ')) == set(expected_uids)
                for instructor in course['instructors']:
                    assert instructor['email'] in instructors
                    assert instructor['name'] in instructors


class TestCoursesChanges:
    """Only admins can see course changes (e.g., room change) that might disrupt scheduled recordings."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_course_changes(client, term_id, expected_status_code=200):
        response = client.get(f'/api/courses/changes/{term_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_course_changes(client, term_id=self.term_id, expected_status_code=401)

    def test_unauthorized(self, client, fake_auth):
        """Instructors cannot see course changes."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_course_changes(client, term_id=self.term_id, expected_status_code=401)

    def test_empty_feed(self, client, admin_session):
        """The /course/changes feed will often be empty."""
        assert len(self._api_course_changes(client, term_id=2192)) == 0

    def test_has_obsolete_room(self, client, admin_session):
        """Admins can see room changes that might disrupt scheduled recordings."""
        course = SisSection.get_course(term_id=self.term_id, section_id=section_2_id)
        actual_room_id = course['meetings'][0]['room']['id']
        obsolete_room = Room.find_room('Barker 101')

        assert obsolete_room
        assert actual_room_id != obsolete_room.id

        _schedule_recordings(
            section_id=section_2_id,
            term_id=self.term_id,
            room_id=obsolete_room.id,
        )
        api_json = self._api_course_changes(client, term_id=self.term_id)
        course = _find_course(api_json=api_json, section_id=section_2_id)
        assert course
        assert course['scheduled']['hasObsoleteRoom'] is True
        assert course['scheduled']['hasObsoleteMeetingTimes'] is False
        assert course['scheduled']['hasObsoleteInstructors'] is False

    def test_has_obsolete_meeting_times(self, client, admin_session):
        """Admins can see meeting time changes that might disrupt scheduled recordings."""
        with test_approvals_workflow(app):
            meeting_days, meeting_start_time, meeting_end_time = get_meeting_data(
                term_id=self.term_id,
                section_id=section_1_id,
            )
            obsolete_meeting_days = 'MOWE'
            assert meeting_days != obsolete_meeting_days

            Scheduled.create(
                instructor_uids=get_instructor_uids(term_id=self.term_id, section_id=section_1_id),
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=obsolete_meeting_days,
                meeting_start_time=meeting_start_time,
                meeting_end_time=meeting_end_time,
                publish_type_='kaltura_my_media',
                recording_type_='presentation_audio',
                room_id=Room.get_room_id(section_id=section_1_id, term_id=self.term_id),
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)

            api_json = self._api_course_changes(client, term_id=self.term_id)
            course = _find_course(api_json=api_json, section_id=section_1_id)
            assert course
            assert course['scheduled']['hasObsoleteRoom'] is False
            assert course['scheduled']['hasObsoleteMeetingTimes'] is True
            assert course['scheduled']['hasObsoleteInstructors'] is False

    def test_has_instructors(self, client, admin_session):
        """Admins can see instructor changes that might disrupt scheduled recordings."""
        with test_approvals_workflow(app):
            meeting_days, meeting_start_time, meeting_end_time = get_meeting_data(
                term_id=self.term_id,
                section_id=section_3_id,
            )
            instructor_uids = get_instructor_uids(term_id=self.term_id, section_id=section_3_id)
            Scheduled.create(
                instructor_uids=instructor_uids + ['100099'],
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=meeting_days,
                meeting_start_time=meeting_start_time,
                meeting_end_time=meeting_end_time,
                publish_type_='kaltura_my_media',
                recording_type_='presenter_audio',
                room_id=Room.get_room_id(section_id=section_3_id, term_id=self.term_id),
                section_id=section_3_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)

            api_json = self._api_course_changes(client, term_id=self.term_id)
            course = _find_course(api_json=api_json, section_id=section_3_id)
            assert course
            assert course['scheduled']['hasObsoleteRoom'] is False
            assert course['scheduled']['hasObsoleteMeetingTimes'] is False
            assert course['scheduled']['hasObsoleteInstructors'] is True
            assert len(course['instructors']) == 1
            assert course['instructors'][0]['name'] == 'Terry Lewis'
            assert course['instructors'][0]['uid'] == '10003'
            assert len(course['scheduled']['instructors']) == 2
            assert {'name': 'Terry Lewis', 'uid': '10003'} in course['scheduled']['instructors']
            assert {'name': '', 'uid': '100099'} in course['scheduled']['instructors']


class TestCrossListedNameGeneration:
    """Rules for collapsing cross-listed courses into a single name/title."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_different_course_names(self, admin_session, client):
        """Departments sharing catalog id and section code."""
        self._verify_name_generation(
            client=client,
            section_id=section_7_id,
            expected_name='MATH C51, LEC 001 | STAT C51, LEC 003',
        )

    def test_different_instruction_format(self, admin_session, client):
        """Departments share catalog id but not section code."""
        self._verify_name_generation(
            client=client,
            section_id=50012,
            expected_name='MATH C51, LEC 001 | STAT C151, COL 001',
        )

    def _verify_name_generation(self, client, section_id, expected_name):
        # section_id = self._create_cross_listed(courses=courses)
        api_json = api_get_course(
            client,
            section_id=section_id,
            term_id=self.term_id,
        )
        assert api_json['label'] == expected_name, f'Failed on section_id={section_id}'

        cross_listings = api_json['crossListings']
        assert len(cross_listings) >= 1
        api_get_course(
            client,
            section_id=cross_listings[0]['sectionId'],
            term_id=self.term_id,
            expected_status_code=404,
        )


class TestUpdatePreferences:
    """Only admins view and modify course preferences. For example, the 'do not email' preference."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_opt_out_update(
            client,
            term_id,
            section_id,
            opt_out,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/opt_out/update',
            data=json.dumps({
                'termId': term_id,
                'sectionId': section_id,
                'optOut': opt_out,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_opt_out_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Instructors cannot modify preferences."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_opt_out_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_authorized(self, client, admin_session):
        """Only admins can toggle the do-not-email preference of any given course."""
        with test_approvals_workflow(app):
            section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=self.term_id)
            previously_opted_out = section_1_id not in section_ids_opted_out
            opt_out = not previously_opted_out
            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=opt_out,
            )
            std_commit(allow_test_environment=True)

            section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=self.term_id)
            if opt_out:
                assert section_1_id in section_ids_opted_out
            else:
                assert section_1_id not in section_ids_opted_out

    def test_scheduling_removes_opt_out(self, client, admin_session):
        with test_approvals_workflow(app):
            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=True,
            )
            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['schedulingStatus'] == 'Not Scheduled'
            assert api_json['hasOptedOut'] is True

            api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presentation_audio',
                section_id=section_1_id,
            )
            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['schedulingStatus'] == 'Queued for Scheduling'
            assert api_json['hasOptedOut'] is False


class TestUnscheduleCourse:
    """Only admins can remove existing approvals and schedules for a course."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_unschedule(
            client,
            term_id,
            section_id,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/unschedule',
            data=json.dumps({
                'termId': term_id,
                'sectionId': section_id,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_unschedule(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Instructors cannot unschedule courses."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_unschedule(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_not_found(self, client, admin_session):
        """A course cannot be unscheduled if can't be found."""
        self._api_unschedule(
            client,
            term_id=self.term_id,
            section_id='99999',
            expected_status_code=400,
        )

    def test_not_scheduled(self, client, admin_session):
        """A course cannot be unscheduled if it hasn't been scheduled or queued first."""
        self._api_unschedule(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=400,
        )

    def test_authorized_unschedule_scheduled(self, client, admin_session):
        with test_approvals_workflow(app):
            api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presentation_audio',
                section_id=section_1_id,
            )
            _schedule_recordings(
                section_id=section_1_id,
                term_id=self.term_id,
            )

            course = api_get_course(client, term_id=self.term_id, section_id=section_1_id)
            assert len(course['approvals']) == 1
            assert course['scheduled'] is not None
            assert course['hasNecessaryApprovals'] is True
            assert course['hasOptedOut'] is False
            assert course['schedulingStatus'] == 'Scheduled'

            response = self._api_unschedule(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
            )
            assert len(response['approvals']) == 0
            assert response['scheduled'] is None
            assert response['hasNecessaryApprovals'] is False
            assert response['hasOptedOut'] is True
            assert response['schedulingStatus'] == 'Not Scheduled'

    def test_authorized_unschedule_queued(self, client, admin_session):
        with test_approvals_workflow(app):
            api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presentation_audio',
                section_id=section_1_id,
            )

            course = api_get_course(client, term_id=self.term_id, section_id=section_1_id)
            assert len(course['approvals']) == 1
            assert course['hasNecessaryApprovals'] is True
            assert course['schedulingStatus'] == 'Queued for Scheduling'

            response = self._api_unschedule(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
            )
            assert len(response['approvals']) == 0
            assert response['schedulingStatus'] == 'Not Scheduled'
            assert response['hasNecessaryApprovals'] is False
            assert response['hasOptedOut'] is True


def _is_course_in_enabled_room(section_id, term_id):
    capability = SisSection.get_course(term_id=term_id, section_id=section_id)['meetings'][0]['room']['capability']
    return capability is not None


def _find_course(api_json, section_id):
    return next((s for s in api_json if s['sectionId'] == section_id), None)


def _schedule_recordings(
        section_id,
        term_id,
        publish_type='kaltura_media_gallery',
        recording_type='presenter_presentation_audio',
        room_id=None,
):
    meeting_days, meeting_start_time, meeting_end_time = get_meeting_data(
        term_id=term_id,
        section_id=section_id,
    )
    Scheduled.create(
        instructor_uids=get_instructor_uids(term_id=term_id, section_id=section_id),
        kaltura_schedule_id=random.randint(1, 10),
        meeting_days=meeting_days,
        meeting_start_time=meeting_start_time,
        meeting_end_time=meeting_end_time,
        publish_type_=publish_type,
        recording_type_=recording_type,
        room_id=room_id or Room.get_room_id(section_id=section_id, term_id=term_id),
        section_id=section_id,
        term_id=term_id,
    )
    std_commit(allow_test_environment=True)
