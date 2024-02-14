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
import json

from diablo.models.email_template import EmailTemplate
import pytest

instructor_uid = '00001'


@pytest.fixture()
def admin_session(fake_auth):
    fake_auth.login('90001')


@pytest.fixture()
def instructor_session(fake_auth):
    fake_auth.login(instructor_uid)


class TestGetAllEmailTemplates:
    """Only Admin users can view and edit email templates."""

    @staticmethod
    def _api_all_email_templates(client, expected_status_code=200):
        response = client.get('/api/email/templates/all')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Deny anonymous access."""
        self._api_all_email_templates(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Deny access if user is not an admin."""
        self._api_all_email_templates(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        email_templates = self._api_all_email_templates(client)
        assert len(email_templates) > 1
        for key in ['id', 'templateType', 'name', 'subjectLine', 'message']:
            assert key in email_templates[0]


class TestGetEmailTemplate:
    """Only Admin users can get email_template info."""

    @staticmethod
    def _api_email_template(client, email_template_id, expected_status_code=200):
        response = client.get(f'/api/email/template/{email_template_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_email_template(client, 1, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_email_template(client, 1, expected_status_code=401)

    def test_email_template_not_found(self, client, admin_session):
        """404 when email_template not found."""
        self._api_email_template(client, email_template_id=999999999, expected_status_code=404)

    def test_get_email_template(self, client, admin_session):
        """Admin user has access to email_template data."""
        email_template = next((t for t in EmailTemplate.all_templates() if 'exorcism' in t.name), None)
        assert email_template
        api_json = self._api_email_template(client, email_template.id)
        assert api_json['id'] == email_template.id
        assert 'exorcism' in api_json['name']


class TestUpdateEmailTemplate:
    """Only Admin users can update an email template."""

    @staticmethod
    def _api_update_email_template(
            client,
            email_template_id,
            template_type,
            name,
            subject_line,
            message,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/email/template/update',
            data=json.dumps({
                'templateId': email_template_id,
                'templateType': template_type,
                'name': name,
                'subjectLine': subject_line,
                'message': message,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def api_update_capability(self, client):
        """Denies anonymous access."""
        self._api_update_email_template(
            client,
            email_template_id=1,
            template_type='notify_instructor_of_changes',
            name='Captain who?',
            subject_line='Captain Howdy.',
            message="Who's Captain Howdy?",
            expected_status_code=401,
        )

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_update_email_template(
            client,
            email_template_id=1,
            template_type='notify_instructor_of_changes',
            name='Captain who?',
            subject_line='Captain Howdy.',
            message="Who's Captain Howdy?",
            expected_status_code=401,
        )

    def test_email_template_not_found(self, client, admin_session):
        """404 when email template not found."""
        self._api_update_email_template(
            client,
            email_template_id=999999999,
            template_type='notify_instructor_of_changes',
            name='Father Dyer',
            subject_line='My idea of Heaven',
            message='My idea of Heaven is a solid white nightclub with me as a headliner for all eternity, and they love me!',
            expected_status_code=404,
        )

    def test_authorized(self, client, admin_session):
        """Admin user has access."""
        email_template_id = 1
        email_template = EmailTemplate.get_template(email_template_id)
        name = f'{email_template.name} (modified)'
        email_template = self._api_update_email_template(
            client,
            email_template_id=email_template.id,
            template_type=email_template.template_type,
            name=name,
            subject_line=email_template.subject_line,
            message=email_template.message,
        )
        assert len(email_template)
        assert email_template['name'] == name


class TestCreateEmailTemplate:
    """Only Admin users can create email templates."""

    @staticmethod
    def _api_create_email_template(
            client,
            template_type,
            name,
            subject_line,
            message,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/email/template/create',
            data=json.dumps({
                'templateType': template_type,
                'name': name,
                'subjectLine': subject_line,
                'message': message,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def api_update_capability(self, client):
        """Denies anonymous access."""
        self._api_create_email_template(
            client,
            template_type='notify_instructor_of_changes',
            name='Captain who?',
            subject_line='Captain Howdy.',
            message="Who's Captain Howdy?",
            expected_status_code=401,
        )

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_create_email_template(
            client,
            template_type='notify_instructor_of_changes',
            name='Captain who?',
            subject_line='Captain Howdy.',
            message="Who's Captain Howdy?",
            expected_status_code=401,
        )

    def test_successful_create(self, client, admin_session):
        """Admin user has success."""
        email_template = self._api_create_email_template(
            client,
            template_type='notify_instructor_of_changes',
            name='Captain who?',
            subject_line='Captain Howdy.',
            message="Who's Captain Howdy?",
        )
        assert 'id' in email_template
        assert email_template['subjectLine'] == 'Captain Howdy.'


class TestGetEmailTemplateCodes:
    """Only Admin users can get email template codes."""

    @staticmethod
    def _api_email_template_codes(client, expected_status_code=200):
        response = client.get('/api/email/template/codes')
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_email_template_codes(client, expected_status_code=401)

    def test_unauthorized(self, client, instructor_session):
        """Denies access if user is not an admin."""
        self._api_email_template_codes(client, expected_status_code=401)

    def test_authorized(self, client, admin_session):
        """Admin user can get template codes."""
        self._api_email_template_codes(client)
