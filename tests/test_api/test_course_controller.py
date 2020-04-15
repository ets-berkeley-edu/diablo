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
import json

from diablo import std_commit
from diablo.models.approval import Approval
from diablo.models.course_preference import CoursePreference
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
import pytest
from tests.test_api.api_test_utils import api_approve, api_get_approvals
from tests.util import test_approvals_workflow

admin_uid = '2040'
deleted_admin_user_uid = '1022796'
section_1_id = 28602
section_1_instructor_uids = ['234567', '8765432']
section_2_id = 28165
section_2_instructor_uids = ['8765432']
section_3_id = 12601
section_with_canvas_course_sites = 22287
section_4_id = 26094
section_5_id = 30563
section_5_instructor_uids = ['234567']


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login('2040')


class TestApprove:
    """Only admins and authorized instructors can sign a course up for Course Capture."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        api_approve(
            client,
            publish_type='canvas',
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

    def test_unauthorized(self, client, db, fake_auth):
        """Deny access if the instructor is not teaching the requested course."""
        fake_auth.login(section_1_instructor_uids[0])
        api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_2_id,
            expected_status_code=403,
        )

    def test_instructor_already_approved(self, client, db, fake_auth):
        """Instructor can submit his/her approval only once."""
        uid = section_1_instructor_uids[0]
        fake_auth.login(uid)

        for expected_status_code in [200, 403]:
            api_approve(
                client,
                publish_type='canvas',
                recording_type='presentation_audio',
                section_id=section_1_id,
                expected_status_code=expected_status_code,
            )

    def test_approval_by_instructors(self, client, db, fake_auth):
        """Instructor can submit approval if s/he is teaching the requested course."""
        fake_auth.login(section_1_instructor_uids[0])
        api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_1_id,
        )
        std_commit(allow_test_environment=True)

        fake_auth.login(section_1_instructor_uids[1])
        api_approve(
            client,
            publish_type='kaltura_media_gallery',
            recording_type='presentation_audio',
            section_id=section_1_id,
        )
        std_commit(allow_test_environment=True)

        for uid in ('234567', '8765432'):
            emails_sent = SentEmail.get_emails_sent_to(uid)
            assert len(emails_sent) > 0
            most_recent = emails_sent[-1]
            assert most_recent.section_id == section_1_id
            assert most_recent.template_type == 'notify_instructor_of_changes'
            assert most_recent.term_id == self.term_id

        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
        )
        assert api_json['room']['location'] == 'Barrows 106'
        instructor_uids = [i['uid'] for i in api_json['instructors']]
        assert instructor_uids == section_1_instructor_uids
        approvals_ = api_json['approvals']
        assert len(approvals_) == 2

        assert approvals_[0]['approvedByUid'] == section_1_instructor_uids[0]
        assert approvals_[0]['publishType'] == 'canvas'

        assert approvals_[1]['approvedByUid'] == section_1_instructor_uids[1]
        assert approvals_[1]['publishType'] == 'kaltura_media_gallery'
        assert approvals_[1]['recordingType'] == 'presentation_audio'
        assert approvals_[1]['recordingTypeName'] == 'Presentation and Audio'

        assert api_json['hasNecessaryApprovals'] is True
        assert api_json['scheduled'] is None

    def test_approval_by_admin(self, client, db, admin_session):
        """Admins can schedule recordings on behalf of any eligible course."""
        api_json = api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_1_id,
        )
        std_commit(allow_test_environment=True)
        assert api_json['hasNecessaryApprovals'] is True
        assert api_json['scheduled'] is None


class TestViewApprovals:
    """Only admins can see all Course Capture sign-ups."""

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        """Deny access if user is not an admin."""
        fake_auth.login(section_1_instructor_uids[0])
        api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
            expected_status_code=403,
        )

    def test_deny_deleted_admin_user(self, client, fake_auth):
        """Deny access if admin user was deleted."""
        fake_auth.login(deleted_admin_user_uid)
        api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_invalid_section_id(self, client, admin_session):
        """404 if section does not exist."""
        api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=999999,
            expected_status_code=404,
        )

    def test_authorized(self, client, db, admin_session):
        """Only admins can review approval status of any given course."""
        api_json = api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
        )
        assert [i['uid'] for i in api_json['instructors']] == ['234567', '8765432']
        assert 'id' in api_json['room']
        assert api_json['room']['location'] == 'Barrows 106'

    def test_date_time_format(self, client, db, fake_auth):
        """Dates and times are properly formatted for front-end display."""
        uid = section_2_instructor_uids[0]
        fake_auth.login(uid)
        api_json = api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert api_json['meetingDays'] == ['MO', 'WE', 'FR']
        assert api_json['meetingStartTime'] == '3:00 pm'
        assert api_json['meetingEndTime'] == '3:59 pm'
        assert api_json['meetingLocation'] == 'Wheeler 150'

    def test_li_ka_shing_recording_options(self, client, db, admin_session):
        """Rooms designated as 'auditorium' offer ALL types of recording."""
        api_json = api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_3_id,
        )
        assert api_json['room']['location'] == 'Li Ka Shing 145'
        assert len(api_json['room']['recordingTypeOptions']) == 3

    def test_section_with_canvas_course_sites(self, client, db, admin_session):
        """Canvas course site information is included in the API."""
        api_json = api_get_approvals(
            client,
            term_id=self.term_id,
            section_id=section_with_canvas_course_sites,
        )
        assert len(api_json['canvasCourseSites']) == 3


class TestCoursesFilter:
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

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_authorized(self, client, db, admin_session):
        with test_approvals_workflow(app):
            room = Room.find_room('Barker 101')
            # First, send invitations
            SentEmail.create(
                section_id=section_5_id,
                recipient_uids=section_5_instructor_uids,
                template_type='invitation',
                term_id=self.term_id,
            )
            SentEmail.create(
                section_id=section_4_id,
                recipient_uids=[admin_uid],
                template_type='invitation',
                term_id=self.term_id,
            )
            # Instructors approve
            Approval.create(
                approved_by_uid=section_5_instructor_uids[0],
                term_id=self.term_id,
                section_id=section_5_id,
                approver_type_='instructor',
                publish_type_='canvas',
                recording_type_='presentation_audio',
                room_id=room.id,
            )
            approval = Approval.create(
                approved_by_uid=admin_uid,
                term_id=self.term_id,
                section_id=section_4_id,
                approver_type_='admin',
                publish_type_='kaltura_media_gallery',
                recording_type_='presenter_audio',
                room_id=room.id,
            )
            meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
                term_id=self.term_id,
                section_id=section_2_id,
            )
            Scheduled.create(
                term_id=self.term_id,
                section_id=section_4_id,
                meeting_days=meeting_days,
                meeting_start_time=meeting_start_time,
                meeting_end_time=meeting_end_time,
                instructor_uids=SisSection.get_instructor_uids(term_id=self.term_id, section_id=section_2_id),
                publish_type_=approval.publish_type,
                recording_type_=approval.recording_type,
                room_id=room.id,
            )
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Invited')

            section_4 = next((s for s in api_json if s['sectionId'] == section_4_id), None)
            assert section_4
            assert len(section_4['approvals']) > 0
            scheduled = section_4.get('scheduled', {})
            assert scheduled.get('publishType') == approval.publish_type
            assert scheduled.get('recordingType') == approval.recording_type

            section_5 = next((s for s in api_json if s['sectionId'] == section_5_id), None)
            assert section_5
            assert len(section_5['approvals']) > 0
            assert section_5['scheduled'] is None
            assert section_5['room'] == room.to_api_json()


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

    def test_unauthorized(self, client, db, fake_auth):
        """Instructors cannot see course changes."""
        fake_auth.login(section_1_instructor_uids[0])
        self._api_course_changes(client, term_id=self.term_id, expected_status_code=401)

    def test_empty_feed(self, client, admin_session):
        """The /course/changes feed will often be empty."""
        assert len(self._api_course_changes(client, term_id=2192)) == 0

    def test_has_obsolete_room(self, client, admin_session):
        """Admins can see room changes that might disrupt scheduled recordings."""
        course = SisSection.get_course(term_id=self.term_id, section_id=section_2_id)
        actual_room_id = course['room']['id']
        obsolete_room = Room.find_room('Barker 101')

        assert obsolete_room
        assert actual_room_id != obsolete_room.id

        meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
            term_id=self.term_id,
            section_id=section_2_id,
        )
        Scheduled.create(
            term_id=self.term_id,
            section_id=section_2_id,
            meeting_days=meeting_days,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            instructor_uids=SisSection.get_instructor_uids(term_id=self.term_id, section_id=section_2_id),
            publish_type_='kaltura_media_gallery',
            recording_type_='presenter_presentation_audio',
            room_id=obsolete_room.id,
        )
        std_commit(allow_test_environment=True)

        course_changes = self._api_course_changes(client, term_id=self.term_id)
        course_change = next((c for c in course_changes if c['sectionId'] == section_2_id), None)
        assert course_change
        assert course_change['scheduled']['hasObsoleteRoom'] is True
        assert course_change['scheduled']['hasObsoleteMeetingTimes'] is False
        assert course_change['scheduled']['hasObsoleteInstructors'] is False

    def test_has_obsolete_meeting_times(self, client, admin_session):
        """Admins can see meeting time changes that might disrupt scheduled recordings."""
        course = SisSection.get_course(term_id=self.term_id, section_id=section_1_id)
        meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
            term_id=self.term_id,
            section_id=section_1_id,
        )
        obsolete_meeting_days = 'MOWE'
        assert meeting_days != obsolete_meeting_days

        Scheduled.create(
            term_id=self.term_id,
            section_id=section_1_id,
            meeting_days=obsolete_meeting_days,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            instructor_uids=SisSection.get_instructor_uids(term_id=self.term_id, section_id=section_1_id),
            publish_type_='canvas',
            recording_type_='presentation_audio',
            room_id=course['room']['id'],
        )
        std_commit(allow_test_environment=True)

        course_changes = self._api_course_changes(client, term_id=self.term_id)
        course_change = next((c for c in course_changes if c['sectionId'] == section_1_id), None)
        assert course_change
        assert course_change['scheduled']['hasObsoleteRoom'] is False
        assert course_change['scheduled']['hasObsoleteMeetingTimes'] is True
        assert course_change['scheduled']['hasObsoleteInstructors'] is False

    def test_has_instructors(self, client, admin_session):
        """Admins can see instructor changes that might disrupt scheduled recordings."""
        course = SisSection.get_course(term_id=self.term_id, section_id=section_3_id)
        meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
            term_id=self.term_id,
            section_id=section_3_id,
        )
        instructor_uids = SisSection.get_instructor_uids(term_id=self.term_id, section_id=section_3_id)
        Scheduled.create(
            term_id=self.term_id,
            section_id=section_3_id,
            meeting_days=meeting_days,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            instructor_uids=instructor_uids + ['999999'],
            publish_type_='canvas',
            recording_type_='presenter_audio',
            room_id=course['room']['id'],
        )
        std_commit(allow_test_environment=True)

        course_changes = self._api_course_changes(client, term_id=self.term_id)
        course_change = next((c for c in course_changes if c['sectionId'] == section_3_id), None)
        assert course_change
        assert course_change['scheduled']['hasObsoleteRoom'] is False
        assert course_change['scheduled']['hasObsoleteMeetingTimes'] is False
        assert course_change['scheduled']['hasObsoleteInstructors'] is True


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

    def test_unauthorized(self, client, db, fake_auth):
        """Instructors cannot modify preferences."""
        fake_auth.login(section_1_instructor_uids[0])
        self._api_opt_out_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_authorized(self, client, admin_session):
        """Only admins can toggle the do-not-email preference of any given course."""
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
