"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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

from tests.util import override_config

admin_uid = '90001'
deleted_admin_user_uid = '910001'
instructor_uid = '10001'
unauthorized_uid = '10000'
no_calnet_record_for_uid = '13'


class TestDevAuth:
    """DevAuth handling."""

    @staticmethod
    def _api_dev_auth_login(client, params, expected_status_code=200):
        response = client.post(
            '/api/auth/dev_auth_login',
            data=json.dumps(params),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return json.loads(response.data)

    def test_dev_auth_is_off(self, app, client):
        """Blocks access unless enabled."""
        with override_config(app, 'DEV_AUTH_ENABLED', False):
            self._api_dev_auth_login(
                client,
                params={
                    'uid': admin_uid,
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
                expected_status_code=404,
            )

    def test_password_fail(self, app, client):
        """Fails if no match on developer password."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            self._api_dev_auth_login(
                client,
                params={
                    'uid': admin_uid,
                    'password': 'Born 2 Lose',
                },
                expected_status_code=401,
            )

    def test_dev_auth_bad_uid(self, app, client):
        """Fails if the chosen UID does not match an authorized user."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            self._api_dev_auth_login(
                client,
                params={
                    'uid': 'A Bad Sort',
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
                expected_status_code=403,
            )

    def test_dev_auth_unauthorized(self, app, client):
        """Deny access to non-admin user with no teaching duties."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            self._api_dev_auth_login(
                client,
                params={
                    'uid': unauthorized_uid,
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
                expected_status_code=403,
            )

    def test_deny_deleted_admin_user(self, app, client):
        """Deny access to deleted admin user."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            self._api_dev_auth_login(
                client,
                params={
                    'uid': deleted_admin_user_uid,
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
                expected_status_code=403,
            )

    def test_dev_auth_for_admin_user(self, app, client):
        """Admin user can log in."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            api_json = self._api_dev_auth_login(
                client,
                params={
                    'uid': admin_uid,
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
            )
            assert api_json['uid'] == admin_uid
            assert api_json['isTeaching'] is False
            assert len(api_json['courses']) == 0
            response = client.get('/api/auth/logout')
            assert response.status_code == 200
            assert response.json['isAnonymous']

    def test_dev_auth_for_instructor(self, app, client):
        """Instructor with one or more sections in current term can log in."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            api_json = self._api_dev_auth_login(
                client,
                params={
                    'uid': instructor_uid,
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
            )
            assert api_json['uid'] == instructor_uid
            assert api_json['isTeaching'] is True
            assert len(api_json['courses']) > 0
            response = client.get('/api/auth/logout')
            assert response.status_code == 200
            assert response.json['isAnonymous']

    def test_user_expired_according_to_calnet(self, app, client):
        """Fails if user has no record in LDAP."""
        with override_config(app, 'DEV_AUTH_ENABLED', True):
            self._api_dev_auth_login(
                client,
                params={
                    'uid': no_calnet_record_for_uid,
                    'password': app.config['DEV_AUTH_PASSWORD'],
                },
                expected_status_code=403,
            )


class TestCasAuth:
    """CAS login URL generation and redirects."""

    def test_cas_login_url(self, client):
        """Returns berkeley.edu URL of CAS login page."""
        response = client.get('/api/auth/cas_login_url')
        assert response.status_code == 200
        assert 'berkeley.edu/cas/login' in response.json.get('casLoginUrl')
