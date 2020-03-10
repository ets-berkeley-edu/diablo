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

from diablo import std_commit
from diablo.models.approval import get_all_recording_types
from flask import current_app as app
from sqlalchemy import text
from tests.test_api.api_test_utils import api_approve, api_get_approvals

admin_uid = '2040'
section_1_id = '28602'
section_1_instructor_uids = ['234567', '8765432']
section_2_id = '28165'
section_2_instructor_uids = ['8765432']
section_3_id = '12601'


class TestApprove:

    def test_not_authenticated(self, client):
        api_approve(
            client,
            publish_type='canvas',
            recording_type='presentation_audio',
            section_id='28602',
            expected_status_code=401,
        )

    def test_invalid_publish_type(self, client, fake_auth):
        fake_auth.login(admin_uid)
        api_approve(
            client,
            publish_type='youtube',
            recording_type='presentation_audio',
            section_id='28602',
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

    def test_instructor_already_approved(self, client, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])

        for expected_status_code in [200, 403]:
            api_approve(
                client,
                publish_type='canvas',
                recording_type='presentation_audio',
                section_id=section_1_id,
                expected_status_code=expected_status_code,
            )

    def test_approval_by_instructors(self, client, db, fake_auth):
        _delete_approvals(db, section_1_id)
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

        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM'],
            section_id=section_1_id,
        )
        assert api_json['section']['room'] == {
            'location': 'Barrows 60',
            'capabilities': [
                {
                    'text': 'Presentation and Audio',
                    'value': 'presentation_audio',
                },
            ],
        }
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
        _delete_approvals(db, section_1_id)
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
        term_id = app.config['CURRENT_TERM']
        api_get_approvals(
            client,
            term_id=term_id,
            section_id='28602',
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        fake_auth.login(section_1_instructor_uids[0])
        term_id = app.config['CURRENT_TERM']
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
            term_id=app.config['CURRENT_TERM'],
            section_id=9999999999,
            expected_status_code=404,
        )

    def test_admin(self, client, fake_auth):
        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM'],
            section_id='28602',
        )
        assert api_json['section']
        assert [i['uid'] for i in api_json['section']['instructors']] == ['234567', '8765432']
        assert api_json['section']['room'] == {
            'location': 'Barrows 60',
            'capabilities': [
                {
                    'text': 'Presentation and Audio',
                    'value': 'presentation_audio',
                },
            ],
        }

    def test_date_time_format(self, client, db, fake_auth):
        _delete_approvals(db, section_2_id)

        fake_auth.login(section_2_instructor_uids[0])
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM'],
            section_id=section_2_id,
        )
        assert api_json['section']
        assert api_json['section']['meetingDays'] == ['MO', 'WE', 'FR']
        assert api_json['section']['meetingStartTime'] == '3:00 pm'
        assert api_json['section']['meetingEndTime'] == '3:59 pm'
        assert api_json['section']['room'] == {
            'location': 'Wheeler 150',
            'capabilities': [],
        }

    def test_li_ka_shing_capture_options(self, client, fake_auth):
        fake_auth.login(admin_uid)
        api_json = api_get_approvals(
            client,
            term_id=app.config['CURRENT_TERM'],
            section_id=section_3_id,
        )
        assert api_json['section']['room']['location'] == 'Li Ka Shing 145'
        assert len(api_json['section']['room']['capabilities']) == len(get_all_recording_types())


def _delete_approvals(db, section_id):
    db.session.execute(text('DELETE FROM approvals WHERE section_id = :section_id'), {'section_id': section_id})
