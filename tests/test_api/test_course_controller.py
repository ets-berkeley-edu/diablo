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
from flask import current_app as app
from tests.test_api.api_test_utils import api_approve, api_get_approvals

admin_uid = '2040'
section_1_id = 28602
section_1_instructor_uids = ['234567', '8765432']
section_2_id = 28165
section_2_instructor_uids = ['8765432']
section_3_id = 12601
section_with_canvas_course_sites = 22287


class TestApprove:

    def test_not_authenticated(self, client):
        api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_invalid_publish_type(self, client, fake_auth):
        fake_auth.login(admin_uid)
        api_approve(
            client,
            publish_type='youtube',
            recording_type='presentation_audio',
            section_id=section_1_id,
            expected_status_code=400,
        )

    def test_unauthorized(self, client, db, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])
        api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_2_id,
            expected_status_code=403,
        )

    def test_instructor_already_approved(self, client, db, fake_auth):
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

        term_id = app.config['CURRENT_TERM_ID']
        for uid in ('234567', '8765432'):
            emails_sent = SentEmail.get_emails_sent_to(uid)
            assert len(emails_sent) > 0
            most_recent = emails_sent[-1]
            assert most_recent.section_id == section_1_id
            assert most_recent.template_type == 'notify_instructor_of_changes'
            assert most_recent.term_id == term_id

        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=term_id,
            section_id=section_1_id,
        )
        assert api_json['room']['location'] == 'Barrows 106'
        instructor_uids = [i['uid'] for i in api_json['section']['instructors']]
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
        assert api_json['scheduled'] is False

    def test_approval_by_admin(self, client, db, fake_auth):
        fake_auth.login(admin_uid)
        api_json = api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id=section_1_id,
        )
        std_commit(allow_test_environment=True)
        assert api_json['hasNecessaryApprovals'] is True
        assert api_json['scheduled'] is False


class TestApprovals:

    def test_not_authenticated(self, client):
        term_id = app.config['CURRENT_TERM_ID']
        api_get_approvals(
            client,
            term_id=term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])
        term_id = app.config['CURRENT_TERM_ID']
        api_get_approvals(
            client,
            term_id=term_id,
            section_id=section_2_id,
            expected_status_code=403,
        )

    def test_invalid_section_id(self, client, fake_auth):
        fake_auth.login(admin_uid)
        api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=999999,
            expected_status_code=404,
        )

    def test_admin(self, client, db, fake_auth):
        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=section_1_id,
        )
        assert api_json['section']
        assert [i['uid'] for i in api_json['section']['instructors']] == ['234567', '8765432']
        assert 'id' in api_json['room']
        assert api_json['room']['location'] == 'Barrows 106'

    def test_date_time_format(self, client, db, fake_auth):
        uid = section_2_instructor_uids[0]
        fake_auth.login(uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=section_2_id,
        )
        assert api_json['section']
        assert api_json['section']['meetingDays'] == ['MO', 'WE', 'FR']
        assert api_json['section']['meetingStartTime'] == '3:00 pm'
        assert api_json['section']['meetingEndTime'] == '3:59 pm'
        assert api_json['section']['meetingLocation'] == 'Wheeler 150'

    def test_li_ka_shing_recording_options(self, client, db, fake_auth):
        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=section_3_id,
        )
        assert api_json['room']['location'] == 'Li Ka Shing 145'
        assert len(api_json['room']['recordingTypeOptions']) == 3

    def test_section_with_canvas_course_sites(self, client, db, fake_auth):
        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=section_with_canvas_course_sites,
        )
        assert len(api_json['section']['canvasCourseSites']) == 3


class TestCoursesFilter:

    @staticmethod
    def _api_courses(client, filter_option=None, term_id=None, expected_status_code=200):
        response = client.post(
            '/api/courses',
            data=json.dumps({
                'termId': term_id or app.config['CURRENT_TERM_ID'],
                'filter': filter_option or 'Not Invited',
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        self._api_courses(client, expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])
        self._api_courses(client, expected_status_code=401)

    def test_authorized(self, client, db, fake_auth):
        term_id = app.config['CURRENT_TERM_ID']
        room = Room.find_room('Barrows 106')
        approval_1 = Approval.create(
            approved_by_uid='234567',
            term_id=term_id,
            section_id=30563,
            approver_type_='instructor',
            publish_type_='canvas',
            recording_type_='presentation_audio',
            room_id=room.id,
        )
        approval_2 = Approval.create(
            approved_by_uid=admin_uid,
            term_id=term_id,
            section_id=26094,
            approver_type_='admin',
            publish_type_='kaltura_media_gallery',
            recording_type_='presenter_audio',
            room_id=room.id,
        )
        scheduled = Scheduled.create(
            term_id=term_id,
            section_id=26094,
            room_id=room.id,
        )
        fake_auth.login(admin_uid)
        api_json = self._api_courses(client)

        section_1 = next((s for s in api_json if s['sectionId'] == 26094), None)
        assert section_1
        assert len(section_1['approvals']) > 0
        assert len(section_1['scheduled']) > 0

        section_2 = next((s for s in api_json if s['sectionId'] == 30563), None)
        assert section_2
        assert len(section_2['approvals']) > 0
        assert len(section_2['scheduled']) == 0
        # Clean up
        Approval.delete(approval_1)
        Approval.delete(approval_2)
        Scheduled.delete(scheduled)


class TestUpdatePreferences:

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
        self._api_opt_out_update(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_unauthorized(self, client, db, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])
        self._api_opt_out_update(
            client,
            term_id=app.config['CURRENT_TERM_ID'],
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        fake_auth.login(admin_uid)
        term_id = app.config['CURRENT_TERM_ID']
        section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)
        previously_opted_out = section_1_id not in section_ids_opted_out
        opt_out = not previously_opted_out
        self._api_opt_out_update(
            client,
            term_id=term_id,
            section_id=section_1_id,
            opt_out=opt_out,
        )
        std_commit(allow_test_environment=True)

        section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)
        if opt_out:
            assert section_1_id in section_ids_opted_out
        else:
            assert section_1_id not in section_ids_opted_out
