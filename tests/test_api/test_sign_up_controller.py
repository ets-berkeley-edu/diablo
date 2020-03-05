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

admin_uid = '2040'
instructor_not_teaching_uid = '1015674'
instructor_uid = '8765432'
section_id = 28602


class TestSignUpStatus:

    @staticmethod
    def _api_sign_up_status(client, term_id_, section_id_, expected_status_code=200):
        response = client.get(f'/api/sign_up/status/{term_id_}/{section_id_}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        term_id = app.config['CURRENT_TERM']
        self._api_sign_up_status(
            client,
            term_id_=term_id,
            section_id_=section_id,
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        fake_auth.login(instructor_not_teaching_uid)
        term_id = app.config['CURRENT_TERM']
        self._api_sign_up_status(
            client,
            term_id_=term_id,
            section_id_=section_id,
            expected_status_code=401,
        )

    def test_invalid_section_id(self, client, fake_auth):
        fake_auth.login(admin_uid)
        self._api_sign_up_status(
            client,
            term_id_=app.config['CURRENT_TERM'],
            section_id_=9999999999,
            expected_status_code=404,
        )

    def test_admin(self, client, fake_auth):
        fake_auth.login(admin_uid)
        api_json = self._api_sign_up_status(
            client,
            term_id_=app.config['CURRENT_TERM'],
            section_id_=section_id,
        )
        assert api_json['section']
        assert api_json['section']['instructorUids'] == ['234567', '8765432']

    def test_instructor(self, client, fake_auth):
        fake_auth.login(instructor_uid)
        api_json = self._api_sign_up_status(
            client,
            term_id_=app.config['CURRENT_TERM'],
            section_id_=section_id,
        )
        assert api_json['section']
        assert api_json['section']['instructorUids'] == ['234567', '8765432']
        assert api_json['signUpStatus']
        assert api_json['signUpStatus']['instructorApprovalUids'] == ['8765432']
        assert api_json['signUpStatus']['publishType'] == 'canvas'
        assert api_json['signUpStatus']['recordingType'] == 'presentation_audio'
