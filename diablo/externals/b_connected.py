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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from smtplib import SMTP

from diablo import skip_when_pytest
from diablo.models.sent_email import SentEmail
from flask import current_app as app


class BConnected:

    def __init__(self):
        self.bcop_smtp_password = app.config['BCOP_SMTP_PASSWORD']
        self.bcop_smtp_port = app.config['BCOP_SMTP_PORT']
        self.bcop_smtp_server = app.config['BCOP_SMTP_SERVER']
        self.bcop_smtp_username = app.config['BCOP_SMTP_USERNAME']

    def send(
            self,
            message,
            recipient,
            subject_line,
            term_id=None,
            section_id=None,
            template_type=None,
    ):
        if not message or not subject_line or not recipient:
            app.logger.error(
                'Attempted to send a message without required fields: '
                f'(recipient={recipient}, subject_line={subject_line}, message={message}')
            return False

        @skip_when_pytest()
        def _send():
            # Connect to SMTP server
            smtp = SMTP(self.bcop_smtp_server, port=self.bcop_smtp_port)
            # TLS encryption
            smtp.starttls()
            smtp.set_debuglevel(app.logger.level == logging.DEBUG)
            smtp.login(self.bcop_smtp_username, self.bcop_smtp_password)

            emails_sent_to = set()

            mock_message = _get_mock_message(
                recipient['name'],
                recipient['email'],
                subject_line,
                message,
            )
            if app.config['DIABLO_ENV'] == 'test':
                app.logger.info(mock_message)
            else:
                from_address = f"{app.config['EMAIL_DIABLO_SUPPORT_FRIENDLY']} <{app.config['EMAIL_DIABLO_SUPPORT']}>"
                to_address = self.get_email_address(user=recipient, subject_line=subject_line)

                msg = MIMEMultipart('alternative')
                msg['From'] = from_address
                msg['To'] = to_address

                if app.config['EMAIL_TEST_MODE']:
                    # Append intended recipient email address to verify when testing.
                    intended_email = recipient['email']
                    msg['Subject'] = f'{subject_line} (To: {intended_email})'
                else:
                    msg['Subject'] = subject_line

                # TODO: 'plain' text version of email?
                msg.attach(MIMEText(message, 'plain'))
                msg.attach(MIMEText(message, 'html'))
                # Send
                smtp.sendmail(from_addr=from_address, to_addrs=to_address, msg=msg.as_string())

                emails_sent_to.add(to_address)

            app.logger.info(f'\'{template_type}\' email sent to {", ".join(list(emails_sent_to))}')
            # Disconnect
            smtp.quit()

        # Send emails
        _send()

        SentEmail.create(
            recipient_uid=recipient['uid'],
            section_id=section_id,
            template_type=template_type,
            term_id=term_id or app.config['CURRENT_TERM_ID'],
        )
        return True

    def ping(self):
        with SMTP(self.bcop_smtp_server, port=self.bcop_smtp_port) as smtp:
            smtp.noop()
            return True

    @classmethod
    def get_email_address(cls, user, subject_line=None):
        user_email = user['email']
        if app.config['EMAIL_TEST_MODE']:
            app.logger.info(f'EMAIL_TEST_MODE intended email: {user_email}; subject_line: {subject_line}')
            return app.config['EMAIL_REDIRECT_WHEN_TESTING']
        else:
            return user_email


def _get_mock_message(recipient_name, email_address, subject_line, message):
    return f"""

        To: {recipient_name} <{email_address}>
        Cc: Course Capture Admin <{app.config['EMAIL_DIABLO_ADMIN']}>
        From: {app.config['EMAIL_DIABLO_SUPPORT_FRIENDLY']} <{app.config['EMAIL_DIABLO_SUPPORT']}>
        Subject: {subject_line}

        Message:
        {message}

    """
