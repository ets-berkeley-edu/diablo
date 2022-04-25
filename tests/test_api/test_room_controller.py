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

from diablo.models.room import Room
import pytest
from tests.util import override_config


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login('90001')


@pytest.fixture()
def instructor_session(fake_auth):
    fake_auth.login('10001')


class TestGetAllRooms:
    """Only Admin users can get info on all rooms."""

    @staticmethod
    def _api_all_rooms(client, expected_status_code=200):
        response = client.get('/api/rooms/all')
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
        for key in ['id', 'capability', 'isAuditorium', 'kalturaResourceId', 'location']:
            assert key in rooms[0]


class TestGetAuditoriums:
    """Only authorized users can get list of auditoriums."""

    @staticmethod
    def _api_auditoriums(client, expected_status_code=200):
        response = client.get('/api/rooms/auditoriums')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_auditoriums(client, expected_status_code=401)

    def test_authorized(self, app, client, instructor_session):
        """Instructors and admins have access."""
        li_ka_shing = 'Li Ka Shing 145'
        expected_locations = ["O'Brien 212", li_ka_shing]
        for cost in [None, 1000]:
            with override_config(app, 'COURSE_CAPTURE_PREMIUM_COST', cost):
                for index, room in enumerate(self._api_auditoriums(client)):
                    assert room['location'] == expected_locations[index]
                    if room['location'] == li_ka_shing:
                        with_operator = room['recordingTypeOptions']['presenter_presentation_audio_with_operator']
                        if cost:
                            assert f'${cost}' in with_operator
                        else:
                            # No dollar sign present
                            assert '$' not in with_operator


class TestGetRoom:
    """Only Admin users can get room info."""

    @staticmethod
    def _api_room(client, room_id, expected_status_code=200):
        response = client.get(f'/api/room/{room_id}')
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

    def test_get_room(self, client, admin_session):
        """Admin user has access to room data."""
        location = "O'Brien 212"
        room = next((r for r in Room.all_rooms() if r.location == location), None)
        assert room
        api_json = self._api_room(client, room.id)
        assert api_json['id'] == room.id
        assert api_json['isAuditorium'] is True
        assert api_json['location'] == location
        assert api_json['kalturaResourceId'] == 890
        assert len(api_json['recordingTypeOptions']) == 1

        # Simple verification of courses sort order
        courses = api_json['courses']
        assert len(courses) > 1

        def _days_first_eligible(course):
            return course['meetings']['eligible'][0]['daysFormatted'][0]

        for index in range(1, len(courses)):
            assert _days_first_eligible(courses[index - 1]) <= _days_first_eligible(courses[index])

    def test_screencast_and_video_auditorium(self, client, admin_session):
        """All recording types are available for Auditorium with 'screencast_and_video' capability."""
        location = 'Li Ka Shing 145'
        room = Room.find_room(location=location)
        assert room
        api_json = self._api_room(client, room.id)
        assert api_json['id'] == room.id
        assert api_json['capabilityName'] == 'Screencast + Video'
        assert api_json['isAuditorium'] is True
        assert api_json['kalturaResourceId'] == 678
        assert api_json['location'] == location
        assert list(api_json['recordingTypeOptions'].keys()) == [
            'presenter_presentation_audio_with_operator',
            'presenter_presentation_audio',
        ]
        # Feed includes courses but room-per-course would be redundant
        assert len(api_json['courses']) > 0
        assert 'room' not in api_json['courses'][0]

    def test_recording_type_options(self, client, admin_session):
        """Available recording types determined by values of capability and is_auditorium."""
        expected = {
            'Barker 101': ['presenter_presentation_audio'],
            "O'Brien 212": ['presentation_audio'],
            'Li Ka Shing 145': [
                'presenter_presentation_audio_with_operator',
                'presenter_presentation_audio',
            ],
        }
        for location, expected_options in expected.items():
            room = Room.find_room(location=location)
            api_json = self._api_room(client, room.id)
            assert list(api_json['recordingTypeOptions'].keys()) == expected_options


class TestUpdateRoomCapability:
    """Only Admin users can update room capability."""

    @staticmethod
    def _api_update_capability(
            client,
            room_id,
            capability,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/room/update_capability',
            data=json.dumps({
                'roomId': room_id,
                'capability': capability,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def api_update_capability(self, client):
        """Denies anonymous access."""
        self._api_update_capability(client, 1, 'screencast_and_video', expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_update_capability(client, 1, 'screencast_and_video', expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        room_id = 1
        room = Room.get_room(room_id)
        capability = 'screencast_and_video' if room.capability == 'screencast' else 'screencast'
        room = self._api_update_capability(client, room_id, capability)
        assert len(room)
        assert room['capability'] == capability


class TestSetRoomAuditorium:
    """Only Admin users can toggle auditorium value."""

    @staticmethod
    def _api_set_auditorium(
            client,
            room_id,
            is_auditorium,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/room/auditorium',
            data=json.dumps({
                'roomId': room_id,
                'isAuditorium': is_auditorium,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def api_update_capability(self, client):
        """Denies anonymous access."""
        self._api_set_auditorium(client, 1, is_auditorium=True, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_set_auditorium(client, 1, is_auditorium=True, expected_status_code=401)

    def test_room_not_found(self, client, admin_session):
        """404 when room not found."""
        self._api_set_auditorium(
            client,
            room_id=999999999,
            is_auditorium=True,
            expected_status_code=404,
        )

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        room_id = 1
        room = Room.get_room(room_id)
        is_auditorium = not room.is_auditorium
        room = self._api_set_auditorium(client, room_id, is_auditorium)
        assert len(room)
        assert room['isAuditorium'] is is_auditorium
