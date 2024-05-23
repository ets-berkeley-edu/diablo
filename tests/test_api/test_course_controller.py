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
import csv
from io import StringIO
import json

from diablo import std_commit
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.emails_job import EmailsJob
from diablo.models.approval import Approval
from diablo.models.opt_out import OptOut
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.test_api.api_test_utils import api_approve, api_get_course, get_instructor_uids, mock_scheduled
from tests.util import override_config, simply_yield, test_approvals_workflow

admin_uid = '90001'
collaborator_uid = '242881'
deleted_admin_user_uid = '910001'
deleted_section_id = 50018
section_1_id = 50000
section_2_id = 50001
section_3_id = 50002
section_4_id = 50004
section_5_id = 50003
section_6_id = 50005
section_7_id = 50010
section_8_id = 50017

section_in_ineligible_room = section_2_id
section_with_canvas_course_sites = section_6_id
eligible_course_with_no_instructors = section_8_id


class TestApprove:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        api_approve(
            client,
            publish_type='kaltura_my_media',
            recording_type='presenter_presentation_audio',
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_invalid_publish_type(self, client, fake_auth):
        """Reject invalid publish types."""
        fake_auth.login(admin_uid)
        api_approve(
            client,
            publish_type='youtube',
            recording_type='presenter_presentation_audio',
            section_id=section_1_id,
            expected_status_code=400,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny access if the instructor is not teaching the requested course."""
        fake_auth.login('10006')
        api_approve(
            client,
            publish_type='kaltura_my_media',
            recording_type='presenter_presentation_audio',
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
                    recording_type='presenter_presentation_audio',
                    section_id=section_1_id,
                    expected_status_code=expected_status_code,
                )

    def test_approval_by_instructors(self, app, client, fake_auth):
        """Instructor can submit approval if s/he is teaching the requested course."""
        with test_approvals_workflow(app):
            course = SisSection.get_course(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            instructors = course['instructors']
            fake_auth.login(instructors[0]['uid'])
            api_approve(
                client,
                instructor_proxies=[{'uid': '10003'}],
                publish_type='kaltura_my_media',
                recording_type='presenter_presentation_audio',
                section_id=section_1_id,
            )
            std_commit(allow_test_environment=True)

            fake_auth.login(instructors[1]['uid'])
            api_approve(
                client,
                instructor_proxies=[{'uid': '10003'}],
                publish_type='kaltura_media_gallery',
                recording_type='presenter_presentation_audio',
                section_id=section_1_id,
            )
            std_commit(allow_test_environment=True)

            EmailsJob(simply_yield).run()

            # First instructor was notified 1) that second instructor needed to approve; 2) that second instructor made changes.
            emails_sent = SentEmail.get_emails_sent_to(instructors[0]['uid'])
            assert len(emails_sent) == 2
            for email in emails_sent:
                assert email.section_id == section_1_id
                assert email.term_id == self.term_id
            assert emails_sent[0].template_type == 'waiting_for_approval'
            assert emails_sent[1].template_type == 'notify_instructor_of_changes'

            # Second instructor received no notifications.
            assert len(SentEmail.get_emails_sent_to(instructors[1]['uid'])) == 0

            fake_auth.login(admin_uid)
            api_json = api_get_course(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
            )
            assert api_json['meetings']['eligible'][0]['room']['location'] == "O'Brien 212"
            instructor_uids = [i['uid'] for i in api_json['instructors']]
            assert instructor_uids == instructor_uids

            assert api_json['scheduled'] is None

    def test_approval_by_admin(self, client, fake_auth):
        """Admins can schedule recordings on behalf of any eligible course."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            api_json = api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presenter_presentation_audio',
                section_id=section_1_id,
            )
            std_commit(allow_test_environment=True)
            assert api_json['scheduled'] is None


class TestGetCourse:

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

    def test_invalid_section_id(self, client, fake_auth):
        """404 if section does not exist."""
        fake_auth.login(admin_uid)
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=999999,
            expected_status_code=404,
        )

    def test_deleted_section(self, client, fake_auth):
        """404 if section does not exist."""
        fake_auth.login(admin_uid)
        assert SisSection.get_course(term_id=self.term_id, section_id=deleted_section_id, include_deleted=True)
        assert not SisSection.get_course(term_id=self.term_id, section_id=deleted_section_id)
        course = api_get_course(
            client,
            term_id=self.term_id,
            section_id=deleted_section_id,
        )
        assert course['deletedAt']

    def test_date_time_format(self, client, fake_auth):
        """Dates and times are properly formatted for front-end display."""
        instructor_uids = get_instructor_uids(section_id=section_2_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert api_json['meetings']['ineligible'][0]['daysFormatted'] == ['MO', 'WE', 'FR']
        assert api_json['meetings']['ineligible'][0]['startTimeFormatted'] == '3:00 pm'
        assert api_json['meetings']['ineligible'][0]['endTimeFormatted'] == '3:59 pm'
        assert api_json['meetings']['ineligible'][0]['location'] == 'Wheeler 150'
        assert api_json['nonstandardMeetingDates'] is False
        assert api_json['meetingType'] == 'A'

    def test_li_ka_shing_recording_options(self, client, fake_auth):
        """Rooms designated as 'auditorium' offer ALL types of recording."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_3_id,
        )
        assert api_json['meetings']['eligible'][0]['room']['location'] == 'Li Ka Shing 145'
        assert len(api_json['meetings']['eligible'][0]['room']['recordingTypeOptions']) == 2

    def test_section_with_canvas_course_sites(self, client, fake_auth):
        """Canvas course site information is included in the API."""
        fake_auth.login(admin_uid)
        CanvasJob(simply_yield).run()
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_with_canvas_course_sites,
        )
        assert len(api_json['canvasCourseSites']) == 3

    def test_administrative_proxy_for_course_page(self, client, fake_auth):
        """Course page includes instructors with APRX role."""
        fake_auth.login(uid=admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=50006,
        )
        assert next((i for i in api_json['instructors'] if i['roleCode'] == 'APRX'), None)

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

    def test_no_cross_listing(self, client, fake_auth):
        """Course does not have cross-listing."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert len(api_json['crossListings']) == 0

    def test_no_instructors(self, client, fake_auth):
        """Course with no instructors should be available."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=eligible_course_with_no_instructors,
        )
        assert len(api_json['instructors']) == 0

    def test_dual_mode_instruction(self, client, fake_auth):
        """Course is both online and in a physical location."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=50014,
        )
        eligible_meetings = api_json['meetings']['eligible']
        ineligible_meetings = api_json['meetings']['ineligible']
        assert len(eligible_meetings) == 1
        assert len(ineligible_meetings) == 2
        assert eligible_meetings[0]['location'] == 'Barker 101'
        assert ineligible_meetings[0]['location'] == 'Internet/Online'
        assert ineligible_meetings[1]['location'] == 'Dwinelle 155'
        assert ineligible_meetings[0]['startDate'] < ineligible_meetings[1]['startDate']
        assert api_json['nonstandardMeetingDates'] is True
        assert api_json['meetingType'] == 'C'

    def test_hybrid_instruction(self, client, fake_auth):
        """Course exists in two concurrent physical locations."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=50015,
        )
        eligible_meetings = api_json['meetings']['eligible']
        ineligible_meetings = api_json['meetings']['ineligible']
        assert len(eligible_meetings) == 1
        assert len(ineligible_meetings) == 1
        assert eligible_meetings[0]['startDate'] == ineligible_meetings[0]['startDate']
        assert api_json['nonstandardMeetingDates'] is False
        assert eligible_meetings[0]['location'] == 'Barker 101'
        assert eligible_meetings[0]['eligible'] is True
        assert ineligible_meetings[0]['location'] == 'LeConte 1'
        assert ineligible_meetings[0]['eligible'] is False
        assert api_json['meetingType'] == 'B'

    def test_meeting_recording_end_date(self, client, fake_auth):
        # The term ends on a Tuesday
        fake_auth.login(admin_uid)
        with override_config(app, 'CURRENT_TERM_END', '2020-11-24'):
            api_json = api_get_course(
                client,
                term_id=self.term_id,
                section_id=50015,
            )
            assert api_json['meetings']['eligible'][0]['endDate'] == '2021-12-11'
            # The course meets on ['MO', 'WE', 'FR']. The last recordings is on Wed preceding term_end
            assert api_json['meetings']['eligible'][0]['recordingEndDate'] == '2021-11-24'
            assert api_json['meetings']['ineligible'][0]['endDate'] == '2021-12-11'
            assert 'recordingEndDate' not in api_json['meetings']['ineligible'][0]


class TestGetCourses:

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
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_do_not_email_filter(self, client, fake_auth):
        """Do Not Email filter: Courses in eligible room; "opt out" is true; all stages of approval; not scheduled."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            # Send invites them opt_out.
            for section_id in (section_1_id, section_in_ineligible_room, section_3_id, section_4_id):
                OptOut.update_opt_out(instructor_uid=admin_uid, section_id=section_id, term_id=self.term_id, opt_out=True)

                in_enabled_room = _is_course_in_enabled_room(section_id=section_id, term_id=self.term_id)
                if section_id == section_in_ineligible_room:
                    # Courses in ineligible rooms will be excluded from the feed.
                    assert not in_enabled_room
                else:
                    assert in_enabled_room
                    _send_invitation_email(section_id, term_id=self.term_id)

            # If course has approvals but not scheduled then it will show up in the feed.
            _create_approval(section_4_id, term_id=self.term_id)
            # Feed will exclude scheduled.
            mock_scheduled(
                section_id=section_3_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)

            api_json = self._api_courses(client, term_id=self.term_id, filter_='Do Not Email')

            # Opted-out courses are in the feed, whether approved or not
            assert _find_course(api_json=api_json, section_id=section_1_id, term_id=self.term_id)
            assert _find_course(api_json=api_json, section_id=section_4_id, term_id=self.term_id)

            for section_id in (section_3_id, section_in_ineligible_room):
                # Excluded courses
                assert not _find_course(api_json=api_json, section_id=section_id, term_id=self.term_id)

    def test_invited_filter(self, client, fake_auth):
        """Invited filter: Course in an eligible room, have received invitation. No approvals. Not scheduled."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            # Past terms should be ignored
            past_term = 2208
            _send_invitation_email(section_id=section_4_id, term_id=past_term)
            _send_invitation_email(section_id=section_5_id, term_id=past_term)
            # Deleted course should be ignored
            _send_invitation_email(section_id=deleted_section_id, term_id=self.term_id)

            # Course with approval is NOT expected in results
            _send_invitation_email(section_id=section_5_id, term_id=self.term_id)
            _create_approval(section_id=section_5_id, term_id=self.term_id)
            # Course in ineligible room is NOT expected in results
            _send_invitation_email(section_id=section_2_id, term_id=self.term_id)
            # Course in eligible room
            eligible_section_id = section_4_id
            _send_invitation_email(section_id=eligible_section_id, term_id=self.term_id)

            std_commit(allow_test_environment=True)

            api_json = self._api_courses(client, term_id=self.term_id, filter_='Invited')
            assert len(api_json) == 1
            assert api_json[0]['sectionId'] == eligible_section_id

            # Section with ZERO approvals will show up in search results
            course = _find_course(api_json=api_json, section_id=section_4_id, term_id=self.term_id)
            assert course
            assert course['label'] == 'CHEM C110L, LAB 001'
            assert course['termId'] == self.term_id
            # The section with approval will NOT show up in search results
            assert not _find_course(api_json=api_json, section_id=section_5_id, term_id=self.term_id)

    def test_not_invited_filter(self, client, fake_auth):
        """Not-invited filter: Courses in eligible rooms, never sent an invitation. No approval. Not scheduled."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            # The first course gets an invitation
            _send_invitation_email(section_1_id, term_id=self.term_id)

            # The second course did not receive an invitation BUT it does have approval.
            invite = SentEmail.get_emails_of_type(
                section_ids=[section_4_id],
                template_type='invitation',
                term_id=self.term_id,
            )
            assert not invite

            _create_approval(section_4_id, term_id=self.term_id)
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Not Invited')
            assert not _find_course(api_json=api_json, section_id=section_1_id, term_id=self.term_id)
            assert not _find_course(api_json=api_json, section_id=section_4_id, term_id=self.term_id)
            assert not _find_course(api_json=api_json, section_id=deleted_section_id, term_id=self.term_id)
            # Zero instructors is acceptable
            assert _find_course(api_json=api_json, section_id=eligible_course_with_no_instructors, term_id=self.term_id)
            # Third course is in enabled room and has not received an invite. Therefore, it is in the feed.
            assert _is_course_in_enabled_room(section_id=section_3_id, term_id=self.term_id)
            course = _find_course(api_json=api_json, section_id=section_3_id, term_id=self.term_id)
            assert course['label'] == 'BIO 1B, LEC 001'

    def test_partially_approved_filter(self, client, fake_auth):
        """Partially approved: Eligible, invited course with 1+ approvals, but not ALL instructors have approved."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            for section_id in [section_1_id, section_6_id, section_7_id]:
                # Assert multiple instructors
                assert len(get_instructor_uids(section_id=section_id, term_id=self.term_id)) > 1
                # Send invites
                _send_invitation_email(section_id, term_id=self.term_id)
                if section_id == section_1_id:
                    # If course is "approved" by admin only then it will NOT show up on the partially-approval list.
                    Approval.create(
                        approved_by_uid=admin_uid,
                        approver_type_='admin',
                        course_display_name=f'term_id:{self.term_id} section_id:{section_id}',
                        publish_type_='kaltura_my_media',
                        recording_type_='presenter_presentation_audio',
                        room_id=Room.get_room_id(section_id=section_id, term_id=self.term_id),
                        section_id=section_id,
                        term_id=self.term_id,
                    )
                else:
                    # Approval by first instructor only
                    _create_approval(section_id=section_id, term_id=self.term_id)

            # Feed will include both scheduled and not scheduled.
            for section_id in [section_1_id, section_7_id]:
                mock_scheduled(section_id=section_id, term_id=self.term_id)

            # Unschedule one of them
            Approval.delete(section_id=section_7_id, term_id=self.term_id)
            Scheduled.delete(section_id=section_7_id, term_id=self.term_id)

            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Partially Approved')
            assert len(api_json) == 1
            course = _find_course(api_json=api_json, section_id=section_6_id, term_id=self.term_id)
            assert course
            assert course['label'] == 'LAW 23, LEC 002'

    def test_scheduled_filter(self, client, fake_auth):
        """Scheduled filter: Courses with recordings scheduled."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            # Send invites
            for section_id in [section_1_id, section_6_id]:
                _send_invitation_email(section_id, term_id=self.term_id)
                _create_approval(section_id, term_id=self.term_id)

            # Feed will only include courses that were scheduled.
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            mock_scheduled(
                section_id=deleted_section_id,
                term_id=self.term_id,
            )
            # Ignore if 'scheduled' record is deleted.
            mock_scheduled(
                section_id=section_2_id,
                term_id=self.term_id,
            )
            Scheduled.delete(section_id=section_2_id, term_id=self.term_id)
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Scheduled')
            assert len(api_json) == 2
            assert _find_course(api_json=api_json, section_id=section_1_id, term_id=self.term_id)
            assert not _find_course(api_json=api_json, section_id=section_6_id, term_id=self.term_id)

    def test_all_filter(self, client, fake_auth):
        """The 'all' filter returns all courses in eligible rooms."""
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            # Put courses in a few different states.
            for section_id in [section_1_id, section_6_id]:
                _send_invitation_email(section_id, term_id=self.term_id)
                _create_approval(section_id, term_id=self.term_id)
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            # We gotta catch 'em all.
            api_json = self._api_courses(client, term_id=self.term_id, filter_='All')
            assert len(api_json) == 11
            for section_id in [section_1_id, section_3_id, section_4_id, section_5_id, section_6_id]:
                assert _find_course(api_json=api_json, section_id=section_id, term_id=self.term_id)
            assert not _find_course(api_json=api_json, section_id=section_in_ineligible_room, term_id=self.term_id)


class TestDownloadCoursesCsv:

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

    def test_download_csv(self, client, fake_auth):
        """Admin users can download courses CSV file."""
        fake_auth.login(admin_uid)
        term_id = app.config['CURRENT_TERM_ID']
        csv_string = self._api_courses_csv(client).decode('utf-8')
        reader = csv.reader(StringIO(csv_string), delimiter=',')
        for index, row in enumerate(reader):
            section_id = row[1]
            meeting_type = row[6]
            sign_up_url = row[9]
            instructors = row[-3]
            instructor_uids = row[-2]
            if index == 0:
                assert section_id == 'Section Id'
                assert meeting_type == 'Meeting Type'
                assert sign_up_url == 'Sign-up URL'
                assert instructors == 'Instructors'
                assert instructor_uids == 'Instructor UIDs'
            else:
                course = SisSection.get_course(section_id=section_id, term_id=term_id)
                assert int(section_id) == course['sectionId']
                for snippet in [app.config['DIABLO_BASE_URL'], section_id, str(term_id)]:
                    assert snippet in sign_up_url

                expected_uids = [instructor['uid'] for instructor in course['instructors']]
                if expected_uids:
                    assert set(instructor_uids.split(', ')) == set(expected_uids)
                else:
                    assert instructor_uids == ''
                for instructor in course['instructors']:
                    assert instructor['email'] in instructors
                    assert instructor['name'] in instructors

                if len(course['meetings']['eligible']) > 1:
                    assert meeting_type == 'D'
                elif course['nonstandardMeetingDates']:
                    assert meeting_type == 'C'
                elif len(course['meetings']['eligible'] + course['meetings']['ineligible']) > 1:
                    assert meeting_type == 'B'
                else:
                    assert meeting_type == 'A'


class TestCrossListedNameGeneration:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_different_course_names(self, client, fake_auth):
        """Departments sharing catalog id and section code."""
        fake_auth.login(admin_uid)
        self._verify_name_generation(
            client=client,
            section_id=section_7_id,
            expected_name='MATH C51, LEC 001 | STAT C51, LEC 003',
        )

    def test_different_instruction_format(self, client, fake_auth):
        """Departments share catalog id but not section code."""
        fake_auth.login(admin_uid)
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


class TestUpdateCollaboratorUids:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_collaborator_uids_update(
            client,
            term_id,
            section_id,
            collaborator_uids,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/collaborator_uids/update',
            data=json.dumps({
                'collaboratorUids': collaborator_uids,
                'sectionId': section_id,
                'termId': term_id,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_collaborator_uids_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            collaborator_uids=[collaborator_uid],
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        fake_auth.login(collaborator_uid)
        self._api_collaborator_uids_update(
            client,
            collaborator_uids=[collaborator_uid],
            section_id=section_1_id,
            term_id=self.term_id,
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Update the 'collaborator_uids' course preference."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        self._api_collaborator_uids_update(
            client,
            collaborator_uids=[collaborator_uid],
            section_id=section_1_id,
            term_id=self.term_id,
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['collaboratorUids'] == [collaborator_uid]


class TestUpdatePublishType:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_publish_type_update(
            client,
            term_id,
            section_id,
            publish_type,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/publish_type/update',
            data=json.dumps({
                'publishType': publish_type,
                'sectionId': section_id,
                'termId': term_id,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        fake_auth.login(collaborator_uid)
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Update the 'publish_type' course preference."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['publishType'] == 'kaltura_my_media'
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['publishType'] == 'kaltura_media_gallery'


class TestUpdateRecordingType:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_recording_type_update(
            client,
            term_id,
            section_id,
            recording_type,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/recording_type/update',
            data=json.dumps({
                'termId': term_id,
                'sectionId': section_id,
                'recordingType': recording_type,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_recording_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            recording_type='presenter_presentation_audio_with_operator',
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        fake_auth.login(collaborator_uid)
        self._api_recording_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            recording_type='presenter_presentation_audio_with_operator',
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Update the 'recording_type' course preference."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['recordingType'] == 'presenter_presentation_audio'
        self._api_recording_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            recording_type='presenter_presentation_audio_with_operator',
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['recordingType'] == 'presenter_presentation_audio_with_operator'


class TestUpdateOptOut:

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
        """Deny non-instructors."""
        fake_auth.login([collaborator_uid])
        self._api_opt_out_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Instructors can toggle the opt-out preference for courses."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        with test_approvals_workflow(app):
            opt_outs = OptOut.get_opt_outs_for_section(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            assert not len(opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False

            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            opt_outs = OptOut.get_opt_outs_for_section(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            assert len(opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is True

            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            opt_outs = OptOut.get_opt_outs_for_section(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            assert not len(opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False

    def test_authorized_blanket_per_term(self, client, fake_auth):
        """Instructors can toggle the opt-out preference for all courses in a term."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        with test_approvals_workflow(app):
            blanket_term_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=self.term_id,
            )
            assert not len(blanket_term_opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False

            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id='all',
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            blanket_term_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=self.term_id,
            )
            assert len(blanket_term_opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is True
            assert course_feed['hasOptedOut'] is True

            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id='all',
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            blanket_term_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=self.term_id,
            )
            assert not len(blanket_term_opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False

    def test_authorized_blanket_all_terms(self, client, fake_auth):
        """Instructors can toggle the opt-out preference for all courses in all terms."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        with test_approvals_workflow(app):
            blanket_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=None,
            )
            assert not len(blanket_opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False

            self._api_opt_out_update(
                client,
                term_id='all',
                section_id='all',
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            blanket_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=None,
            )
            assert len(blanket_opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is True
            assert course_feed['hasOptedOut'] is True

            self._api_opt_out_update(
                client,
                term_id='all',
                section_id='all',
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            blanket_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=None,
            )
            assert not len(blanket_opt_outs)
            course_feed = _api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False

    def test_scheduling_removes_opt_out(self, client, fake_auth):
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            self._api_opt_out_update(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=True,
            )
            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['hasOptedOut'] is True

            api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presenter_presentation_audio',
                section_id=section_1_id,
            )
            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['hasOptedOut'] is False


class TestUnscheduleCourse:

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

    def test_not_found(self, client, fake_auth):
        """A course cannot be unscheduled if can't be found."""
        fake_auth.login(admin_uid)
        self._api_unschedule(
            client,
            term_id=self.term_id,
            section_id='99999',
            expected_status_code=400,
        )

    def test_not_scheduled(self, client, fake_auth):
        """A course cannot be unscheduled if it hasn't been scheduled or queued first."""
        fake_auth.login(admin_uid)
        self._api_unschedule(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=400,
        )

    def test_authorized_unschedule_scheduled(self, client, fake_auth):
        fake_auth.login(admin_uid)
        with test_approvals_workflow(app):
            api_approve(
                client,
                publish_type='kaltura_my_media',
                recording_type='presenter_presentation_audio',
                section_id=section_1_id,
            )
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )

            course = api_get_course(client, term_id=self.term_id, section_id=section_1_id)
            assert len(course['scheduled']) == 1
            assert course['hasOptedOut'] is False

            response = self._api_unschedule(
                client,
                term_id=self.term_id,
                section_id=section_1_id,
            )
            assert response['scheduled'] is None
            assert response['hasOptedOut'] is True


class TestCoursesReport:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_courses_report(client, term_id, expected_status_code=200):
        response = client.get(f'/api/courses/report/{term_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses_report(client, term_id=self.term_id, expected_status_code=401)

    def test_unauthorized(self, client, fake_auth):
        """Instructors cannot view courses report."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_courses_report(client, term_id=self.term_id, expected_status_code=401)

    def test_total_scheduled_count(self, client, fake_auth):
        """The courses report includes valid total_scheduled_count."""
        fake_auth.login(admin_uid)
        report = self._api_courses_report(client, term_id=self.term_id)
        assert report['totalScheduledCount'] == len(Scheduled.get_all_scheduled(self.term_id))


def _api_get_course(client, term_id, section_id, expected_status_code=200):
    response = client.get(f'/api/course/{term_id}/{section_id}')
    assert response.status_code == expected_status_code
    return response.json


def _create_approval(section_id, term_id):
    Approval.create(
        approved_by_uid=get_instructor_uids(section_id=section_id, term_id=term_id)[0],
        approver_type_='instructor',
        course_display_name=f'term_id:{term_id} section_id:{section_id}',
        publish_type_='kaltura_my_media',
        recording_type_='presenter_presentation_audio',
        room_id=Room.get_room_id(section_id=section_id, term_id=term_id),
        section_id=section_id,
        term_id=term_id,
    )


def _find_course(api_json, section_id, term_id):
    return next((s for s in api_json if s['sectionId'] == section_id and s['termId'] == term_id), None)


def _is_course_in_enabled_room(section_id, term_id):
    eligible_meetings = SisSection.get_course(term_id=term_id, section_id=section_id)['meetings']['eligible']
    return eligible_meetings and eligible_meetings[0]['room']['capability'] is not None


def _send_invitation_email(section_id, term_id):
    SentEmail.create(
        section_id=section_id,
        recipient_uid=get_instructor_uids(section_id=section_id, term_id=term_id)[0],
        template_type='invitation',
        term_id=term_id,
    )
