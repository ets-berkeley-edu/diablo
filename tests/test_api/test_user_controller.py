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
import pytest

admin_uid = '90001'
instructor_not_teaching_uid = '10000'
instructor_uid = '10001'


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login(admin_uid)


@pytest.fixture()
def instructor_session(fake_auth):
    fake_auth.login(instructor_uid)


class TestMyProfile:

    @staticmethod
    def _api_my_profile(client, expected_status_code=200):
        response = client.get('/api/user/my_profile')
        assert response.status_code == expected_status_code
        return response.json

    def test_instructor_not_teaching_uid(self, client, fake_auth):
        fake_auth.login(instructor_not_teaching_uid)
        api_json = self._api_my_profile(client)
        assert api_json['isActive'] is False
        assert api_json['isAnonymous'] is True
        assert api_json['isAuthenticated'] is False
        assert api_json['uid'] is None

    def test_admin_is_active(self, admin_session, client, fake_auth):
        api_json = self._api_my_profile(client)
        assert api_json['isActive'] is True
        assert api_json['isAnonymous'] is False
        assert api_json['isAuthenticated'] is True
        assert api_json['uid'] == admin_uid
        assert api_json['isTeaching'] is False
        assert api_json['courses'] == []

    def test_instructor(self, client, fake_auth, instructor_session):
        api_json = self._api_my_profile(client)
        assert api_json['isActive'] is True
        assert api_json['isAnonymous'] is False
        assert api_json['isAuthenticated'] is True
        assert api_json['isTeaching'] is True
        assert api_json['uid'] == instructor_uid

        sections = api_json['courses']
        assert sections[0]['courseTitle'] == 'Data Structures'
        assert sections[0]['sectionId'] == 50001

        assert sections[1]['courseTitle'] == 'Foundations of Data Science'
        assert sections[1]['sectionId'] == 50000
        assert [i['uid'] for i in sections[1]['instructors']] == [instructor_uid, '10002']


class TestUserProfile:
    """Admin user see all user profiles."""

    @staticmethod
    def _api_user(client, uid, expected_status_code=200):
        response = client.get(f'/api/user/{uid}')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_user(client, instructor_uid, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_user(client, instructor_uid, expected_status_code=401)

    def test_user_not_found(self, client, admin_session):
        """404 when user not found."""
        self._api_user(client, uid='99999', expected_status_code=404)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        user = self._api_user(client, instructor_uid)
        assert user
        assert user['uid'] == instructor_uid
        courses = user.get('courses')
        assert len(courses) > 0

        for course in courses:
            assert 'approvals' in course
            assert 'scheduled' in course
            instructor = next((i for i in course['instructors'] if i['uid'] == instructor_uid), None)
            assert instructor

    def test_only_courses_taught_by_instructor(self, client, admin_session):
        """Includes only courses taught by instructor."""
        def find_course(section_id):
            return next((c for c in user.get('courses') if c['sectionId'] == section_id), None)

        user = self._api_user(client, instructor_uid)
        assert find_course(50000)
        assert not find_course(50006)


class TestAdminUsers:
    """Admin user has access to all admin user profiles."""

    @staticmethod
    def _api_admin_users(client, expected_status_code=200):
        response = client.get('/api/users/admins')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_admin_users(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_admin_users(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        admin_users = self._api_admin_users(client)
        assert len(admin_users) > 0
        for admin_user in admin_users:
            assert 'email' in admin_user
            assert 'name' in admin_user
            assert 'uid' in admin_user
