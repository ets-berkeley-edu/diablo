"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.models.blackout import Blackout
import pytest

instructor_uid = '00001'


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login('90001')


@pytest.fixture()
def instructor_session(fake_auth):
    fake_auth.login(instructor_uid)


class TestGetBlackouts:
    """Only Admin users can view and edit blackouts."""

    @staticmethod
    def _api_all_blackouts(client, expected_status_code=200):
        response = client.get('/api/blackouts/all')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Deny anonymous access."""
        self._api_all_blackouts(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Deny access if user is not an admin."""
        self._api_all_blackouts(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        blackouts = self._api_all_blackouts(client)
        assert len(blackouts) > 0
        for key in ['id', 'name', 'startDate', 'endDate']:
            assert key in blackouts[0]


class TestGetBlackout:
    """Only Admin users can get blackout info."""

    @staticmethod
    def _api_blackout(client, blackout_id, expected_status_code=200):
        response = client.get(f'/api/blackout/{blackout_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_blackout(client, 1, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_blackout(client, 1, expected_status_code=401)

    def test_blackout_not_found(self, client, admin_session):
        """404 when blackout not found."""
        self._api_blackout(client, blackout_id=999999999, expected_status_code=404)

    def test_get_blackout(self, client, admin_session):
        """Admin user has access to blackout data."""
        blackout = next((t for t in Blackout.all_blackouts() if 'exorcism' in t.name), None)
        assert blackout
        api_json = self._api_blackout(client, blackout.id)
        assert api_json['id'] == blackout.id
        assert 'exorcism' in api_json['name']


class TestUpdateBlackout:
    """Only Admin users can update an blackout."""

    @staticmethod
    def _api_update_blackout(
            client,
            blackout_id,
            name,
            start_date,
            end_date,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/blackout/update',
            data=json.dumps({
                'blackoutId': blackout_id,
                'name': name,
                'startDate': start_date,
                'endDate': end_date,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def api_update_capability(self, client):
        """Denies anonymous access."""
        self._api_update_blackout(
            client,
            blackout_id=1,
            name='Thanksgiving 2021',
            start_date='11/25/2021',
            end_date='11/26/2021',
            expected_status_code=401,
        )

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_update_blackout(
            client,
            blackout_id=1,
            name='Thanksgiving 2021',
            start_date='11/25/2021',
            end_date='11/26/2021',
            expected_status_code=401,
        )

    def test_blackout_not_found(self, client, admin_session):
        """404 when blackout not found."""
        self._api_update_blackout(
            client,
            blackout_id=999999999,
            name='Thanksgiving 2021',
            start_date='11/25/2021',
            end_date='11/26/2021',
            expected_status_code=404,
        )

    def test_authorized(self, client, admin_session):
        """Admin user can update blackout dates."""
        blackout = Blackout.create(
            name='Bloomsday',
            start_date='2020-06-16',
            end_date='2020-06-16',
        )
        std_commit(allow_test_environment=True)

        blackout = Blackout.get_blackout(blackout.id)
        name = f'{blackout.name} (modified)'
        blackout = self._api_update_blackout(
            client,
            blackout_id=blackout.id,
            name=name,
            start_date='2021-06-16',
            end_date='2021-06-16',
        )
        assert len(blackout)
        assert blackout['name'] == name
        assert blackout['startDate'] == '2021-06-16'
        assert blackout['endDate'] == '2021-06-16'


class TestCreateBlackout:
    """Only Admin users can create blackouts."""

    @staticmethod
    def _api_create_blackout(
            client,
            name,
            start_date,
            end_date,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/blackout/create',
            data=json.dumps({
                'name': name,
                'startDate': start_date,
                'endDate': end_date,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def api_update_capability(self, client):
        """Denies anonymous access."""
        self._api_create_blackout(
            client,
            name='Thanksgiving 2021',
            start_date='2021-11-25',
            end_date='2021-11-26',
            expected_status_code=401,
        )

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_create_blackout(
            client,
            name='Thanksgiving 2021',
            start_date='2021-11-25',
            end_date='2021-11-26',
            expected_status_code=401,
        )

    def test_overlapping_date_ranges(self, client, admin_session):
        """Expect error when blackout dates overlap."""
        Blackout.create(
            name='Final exams',
            start_date='2021-12-13',
            end_date='2021-12-17',
        )
        std_commit(allow_test_environment=True)
        self._api_create_blackout(
            client,
            name='Boston Tea Party week',
            start_date='2021-12-16',
            end_date='2021-12-23',
            expected_status_code=400,
        )

    def test_successful_create(self, client, admin_session):
        """Admin user has success."""
        name = 'Thanksgiving 2021'
        blackout = self._api_create_blackout(
            client,
            name=name,
            start_date='2021-11-25',
            end_date='2021-11-26',
        )
        assert 'id' in blackout
        assert blackout['name'] == name
