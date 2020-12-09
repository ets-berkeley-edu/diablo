"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.models.sent_email import SentEmail


class TestErrorHandler:
    """Send system_error_email when server-side exception."""

    def test_system_error_email_when_error(self, client, fake_auth):
        """All users, even anonymous, can get version info."""
        fake_auth.login('90001')
        sent_email_count = _system_error_email_count()
        assert client.get('/api/ping').status_code == 200
        assert _system_error_email_count() == sent_email_count + 1

    def test_no_system_error_email_when_404(self, app, client):
        """All users, even anonymous, can get version info."""
        sent_email_count = _system_error_email_count()
        response = client.get('/api/foo')
        assert response.status_code == 404
        assert _system_error_email_count() == sent_email_count

    def test_no_system_error_email_when_wrong_method(self, app, client):
        """All users, even anonymous, can get version info."""
        sent_email_count = _system_error_email_count()
        response = client.post('/api/config')
        assert response.status_code != 200
        assert _system_error_email_count() == sent_email_count


def _system_error_email_count():
    return len(SentEmail.get_emails_sent_to('0'))
