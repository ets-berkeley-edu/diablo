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
from diablo.models.sent_email import SentEmail
from flask import current_app as app


class Mailgun:

    def __init__(self):
        self.email_redirect_when_testing = app.config['EMAIL_REDIRECT_WHEN_TESTING']
        self.use_actual_address = app.config.get('EB_ENVIRONMENT', None) == 'diablo-prod'

    def send(self, message, recipients, subject_line, term_id=None, section_id=None, template_type=None):
        for recipient in recipients:
            email_address = recipient['email'] if self.use_actual_address else self.email_redirect_when_testing
            if app.config['DIABLO_ENV'] == 'test':
                app.logger.info(_get_mock_message(recipient['name'], email_address, subject_line, message))
            else:
                # TODO: Implement according to https://documentation.mailgun.com/en/latest/quickstart-sending.html#send-via-api
                app.logger.info(_get_mock_message(recipient['name'], email_address, subject_line, message))
        SentEmail.create(
            recipient_uids=[recipient['uid'] for recipient in recipients],
            section_id=section_id,
            template_type=template_type,
            term_id=term_id or app.config['CURRENT_TERM_ID'],
        )

    def ping(self):
        return self.use_actual_address


def _get_mock_message(recipient_name, email_address, subject_line, message):
    return f"""

        To: {recipient_name}<{email_address}>
        From: {app.config['EMAIL_DIABLO_SUPPORT']}
        Subject: {subject_line}

        Message:
        {message}

    """
