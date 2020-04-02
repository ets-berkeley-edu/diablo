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

EMAILS_SENT_IN_TEST_MODE = []


def send_email(recipient_name, email_address, subject_line, message):
    if app.config['DIABLO_ENV'] == 'test':
        EMAILS_SENT_IN_TEST_MODE.append(_get_mock_message(recipient_name, email_address, subject_line, message))
    else:
        # TODO: Implement according to https://documentation.mailgun.com/en/latest/quickstart-sending.html#send-via-api
        app.logger.info(_get_mock_message(recipient_name, email_address, subject_line, message))


def mailgun_ping():
    return True


def _get_mock_message(recipient_name, email_address, subject_line, message):
    return f"""

        To: {recipient_name}<{email_address}>
        From: {app.config['EMAIL_DIABLO_SUPPORT']}
        Subject: {subject_line}

        Message:
        {message}

    """
