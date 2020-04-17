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
section_2_id = 28165
section_3_id = 12601
section_4_id = 26094
section_5_id = 30563
section_6_id = 22287

section_in_ineligible_room = section_2_id
section_with_canvas_course_sites = section_6_id


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
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_2_id,
            expected_status_code=403,
        )

    def test_instructor_already_approved(self, client, db, fake_auth):
        """Instructor can submit his/her approval only once."""
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

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
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_approve(
            client,
            publish_type='canvas',
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
        assert instructor_uids == instructor_uids
        approvals_ = api_json['approvals']
        assert len(approvals_) == 2

        assert approvals_[0]['approvedByUid'] == instructor_uids[0]
        assert approvals_[0]['publishType'] == 'canvas'

        assert approvals_[1]['approvedByUid'] == instructor_uids[1]
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
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
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
        instructor_uids = _get_instructor_uids(section_id=section_2_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
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
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_do_not_email_filter(self, client, db, admin_session):
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
                    SentEmail.create(
                        section_id=section_id,
                        recipient_uids=_get_instructor_uids(section_id=section_id, term_id=self.term_id),
                        template_type='invitation',
                        term_id=self.term_id,
                    )

            # If course has approvals but not scheduled then it will show up in the feed.
            Approval.create(
                approved_by_uid=_get_instructor_uids(section_id=section_1_id, term_id=self.term_id)[0],
                term_id=self.term_id,
                section_id=section_1_id,
                approver_type_='instructor',
                publish_type_='canvas',
                recording_type_='presentation_audio',
                room_id=Room.get_room_id(section_id=section_1_id, term_id=self.term_id),
            )
            # Feed will exclude scheduled.
            _schedule_recordings(
                section_id=section_3_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)

            api_json = self._api_courses(client, term_id=self.term_id, filter_='Do Not Email')
            for section_id in (section_1_id, section_4_id):
                # The 'Do Not Email' course is in the feed
                assert _find_course(api_json=api_json, section_id=section_id)

            for section_id in (section_3_id, section_in_ineligible_room):
                # Excluded courses
                assert not _find_course(api_json=api_json, section_id=section_id)

    def test_invited_filter(self, client, db, admin_session):
        """Invited filter: Course in an eligible room, have received invitation. No approvals. Not scheduled."""
        with test_approvals_workflow(app):
            # First, send invitations
            SentEmail.create(
                section_id=section_4_id,
                recipient_uids=_get_instructor_uids(section_id=section_4_id, term_id=self.term_id),
                template_type='invitation',
                term_id=self.term_id,
            )
            section_5_instructor_uids = _get_instructor_uids(section_id=section_5_id, term_id=self.term_id)
            SentEmail.create(
                section_id=section_5_id,
                recipient_uids=section_5_instructor_uids,
                template_type='invitation',
                term_id=self.term_id,
            )
            # The section with approval will NOT show up in search results
            Approval.create(
                approved_by_uid=section_5_instructor_uids[0],
                term_id=self.term_id,
                section_id=section_5_id,
                approver_type_='instructor',
                publish_type_='canvas',
                recording_type_='presentation_audio',
                room_id=SisSection.get_course(term_id=self.term_id, section_id=section_5_id)['room']['id'],
            )
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Invited')
            # Section with ZERO approvals will show up in search results
            course = _find_course(api_json=api_json, section_id=section_4_id)
            assert course
            assert course['label'] == 'CHEM C110L, LAB 001'
            # The section with approval will NOT show up in search results
            assert not _find_course(api_json=api_json, section_id=section_5_id)

    def test_not_invited_filter(self, client, db, admin_session):
        """Not-invited filter: Courses in eligible rooms, never sent an invitation. No approval. Not scheduled."""
        with test_approvals_workflow(app):
            # The first course gets an invitation
            section_1_instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            SentEmail.create(
                section_id=section_1_id,
                recipient_uids=section_1_instructor_uids,
                template_type='invitation',
                term_id=self.term_id,
            )
            # The second course did not receive an invitation BUT it does have approval.
            invite = SentEmail.get_emails_of_type(
                section_id=section_4_id,
                template_type='invitation',
                term_id=self.term_id,
            )
            assert not invite
            Approval.create(
                approved_by_uid=_get_instructor_uids(section_id=section_4_id, term_id=self.term_id)[0],
                term_id=self.term_id,
                section_id=section_4_id,
                approver_type_='instructor',
                publish_type_='canvas',
                recording_type_='presentation_audio',
                room_id=Room.get_room_id(section_id=section_4_id, term_id=self.term_id),
            )
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Not Invited')
            assert not _find_course(api_json=api_json, section_id=section_1_id)
            assert not _find_course(api_json=api_json, section_id=section_4_id)
            # Third course is in enabled room and has not received an invite. Therefore, it is in the feed.
            assert _is_course_in_enabled_room(section_id=section_3_id, term_id=self.term_id)
            course = _find_course(api_json=api_json, section_id=section_3_id)
            assert course
            assert course['label'] == 'BIO 1B, LEC 001'

    def test_partially_approved_filter(self, client, db, admin_session):
        """Partially approved: Eligible, invited course with 1+ approvals, but not ALL instructors have approved."""
        with test_approvals_workflow(app):
            # Assert multiple instructors
            section_1_instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            section_6_instructor_uids = _get_instructor_uids(section_id=section_6_id, term_id=self.term_id)
            assert len(section_1_instructor_uids) > 1
            assert len(section_6_instructor_uids) > 1
            # Send invites
            courses = [
                {'section_id': section_1_id, 'instructor_uids': section_1_instructor_uids},
                {'section_id': section_6_id, 'instructor_uids': section_6_instructor_uids},
            ]
            for course in courses:
                SentEmail.create(
                    section_id=course['section_id'],
                    recipient_uids=course['instructor_uids'],
                    template_type='invitation',
                    term_id=self.term_id,
                )
                Approval.create(
                    approved_by_uid=course['instructor_uids'][0],
                    term_id=self.term_id,
                    section_id=course['section_id'],
                    approver_type_='instructor',
                    publish_type_='canvas',
                    recording_type_='presentation_audio',
                    room_id=Room.get_room_id(section_id=course['section_id'], term_id=self.term_id),
                )
            # Feed will include both scheduled and not scheduled.
            _schedule_recordings(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Partially Approved')
            assert len(api_json) == 2
            assert _find_course(api_json=api_json, section_id=section_1_id)
            course = _find_course(api_json=api_json, section_id=section_6_id)
            assert course
            assert course['label'] == 'LAW 23, LEC 002'

    def test_scheduled_filter(self, client, db, admin_session):
        """Scheduled filter: Courses with recordings scheduled."""
        with test_approvals_workflow(app):
            section_1_instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            section_6_instructor_uids = _get_instructor_uids(section_id=section_6_id, term_id=self.term_id)
            # Send invites
            courses = [
                {'section_id': section_1_id, 'instructor_uids': section_1_instructor_uids},
                {'section_id': section_6_id, 'instructor_uids': section_6_instructor_uids},
            ]
            for course in courses:
                SentEmail.create(
                    section_id=course['section_id'],
                    recipient_uids=course['instructor_uids'],
                    template_type='invitation',
                    term_id=self.term_id,
                )
                Approval.create(
                    approved_by_uid=course['instructor_uids'][0],
                    term_id=self.term_id,
                    section_id=course['section_id'],
                    approver_type_='instructor',
                    publish_type_='canvas',
                    recording_type_='presentation_audio',
                    room_id=Room.get_room_id(section_id=course['section_id'], term_id=self.term_id),
                )
            # Feed will only include courses that were scheduled.
            _schedule_recordings(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Scheduled')
            assert len(api_json) == 1
            assert _find_course(api_json=api_json, section_id=section_1_id)
            assert not _find_course(api_json=api_json, section_id=section_6_id)


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
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
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
                room_id=Room.get_room_id(section_id=section_1_id, term_id=self.term_id),
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
                room_id=Room.get_room_id(section_id=section_3_id, term_id=self.term_id),
            )
            std_commit(allow_test_environment=True)

            api_json = self._api_course_changes(client, term_id=self.term_id)
            course = _find_course(api_json=api_json, section_id=section_3_id)
            assert course
            assert course['scheduled']['hasObsoleteRoom'] is False
            assert course['scheduled']['hasObsoleteMeetingTimes'] is False
            assert course['scheduled']['hasObsoleteInstructors'] is True


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
        instructor_uids = _get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
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


def _is_course_in_enabled_room(section_id, term_id):
    capability = SisSection.get_course(term_id=term_id, section_id=section_id)['room']['capability']
    return capability is not None


def _find_course(api_json, section_id):
    return next((s for s in api_json if s['sectionId'] == section_id), None)


def _get_instructor_uids(section_id, term_id):
    return SisSection.get_instructor_uids(term_id=term_id, section_id=section_id)


def _schedule_recordings(
        section_id,
        term_id,
        publish_type='kaltura_media_gallery',
        recording_type='presenter_presentation_audio',
        room_id=None,
):
    meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
        term_id=term_id,
        section_id=section_id,
    )
    Scheduled.create(
        term_id=term_id,
        section_id=section_id,
        meeting_days=meeting_days,
        meeting_start_time=meeting_start_time,
        meeting_end_time=meeting_end_time,
        instructor_uids=SisSection.get_instructor_uids(term_id=term_id, section_id=section_id),
        publish_type_=publish_type,
        recording_type_=recording_type,
        room_id=room_id or Room.get_room_id(section_id=section_id, term_id=term_id),
    )
    std_commit(allow_test_environment=True)
