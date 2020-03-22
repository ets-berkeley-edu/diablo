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
from diablo.models.room import Room
import pytest


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login('2040')


@pytest.fixture()
def instructor_session(fake_auth):
    fake_auth.login('8765432')


class TestGetAllRooms:
    """Only Admin users can get info on all rooms."""

    @staticmethod
    def _api_all_rooms(client, expected_status_code=200):
        response = client.get('/api/berkeley/all_rooms')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_all_rooms(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_all_rooms(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        rooms = self._api_all_rooms(client)
        assert len(rooms)
        for key in ['id', 'location', 'capability']:
            assert key in rooms[0]


class TestGetRoom:
    """Only Admin users can get room info."""

    @staticmethod
    def _api_room(client, room_id, expected_status_code=200):
        response = client.get(f'/api/berkeley/room/{room_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_room(client, 1, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_room(client, 1, expected_status_code=401)

    def test_room_not_found(self, client, admin_session):
        """404 when room not found."""
        self._api_room(client, room_id=999999999, expected_status_code=404)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        room = self._api_room(client, 1)
        assert len(room)
        assert room['id'] == 1

        room_from_db = Room.get_room(1)
        assert room['location'] == room_from_db.location
        assert room['capability'] == room_from_db.capability
