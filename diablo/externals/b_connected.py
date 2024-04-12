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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from smtplib import SMTP

from diablo import skip_when_pytest
from diablo.lib.util import get_eb_environment
from diablo.models.cross_listing import CrossListing
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

        eb_env = get_eb_environment()
        prefix = '' if 'prod' in (eb_env or '') else f"[{eb_env or 'diablo-local'}] "
        subject_line = f'{prefix}{subject_line}'

        @skip_when_pytest()
        def _send():
            smtp = SMTP(self.bcop_smtp_server, port=self.bcop_smtp_port)
            # TLS encryption
            smtp.starttls()
            smtp.set_debuglevel(app.logger.level == logging.DEBUG)
            smtp.login(self.bcop_smtp_username, self.bcop_smtp_password)

            emails_sent_to = set()

            if app.config['DIABLO_ENV'] == 'test':
                write_email_to_log(message=message, recipient=recipient, subject_line=subject_line)
            else:
                from_address = f"{app.config['EMAIL_COURSE_CAPTURE_SUPPORT_LABEL']} <{app.config['EMAIL_COURSE_CAPTURE_SUPPORT']}>"

                for email_address in self.get_email_addresses(user=recipient):
                    msg = MIMEMultipart('alternative')
                    msg['From'] = from_address
                    msg['To'] = email_address

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
                    smtp.sendmail(from_addr=from_address, to_addrs=email_address, msg=msg.as_string())

                    emails_sent_to.add(email_address)

            phrase = f"email sent to {', '.join(list(emails_sent_to))}"
            app.logger.info(f'{template_type.capitalize()} {phrase}' if template_type else f'Alert {phrase}')
            # Disconnect
            smtp.quit()

        # Send emails
        _send()

        recipient_uid = recipient['uid']
        term_id = term_id or app.config['CURRENT_TERM_ID']
        SentEmail.create(
            recipient_uid=recipient_uid,
            section_id=section_id,
            template_type=template_type,
            term_id=term_id,
        )
        if template_type != 'semester_start':
            for cross_listed_section_id, instructor_uids in CrossListing.get_instructor_uids_of_cross_listed_sections(
                section_id=section_id,
                term_id=term_id,
            ).items():
                if recipient_uid in instructor_uids:
                    SentEmail.create(
                        recipient_uid=recipient_uid,
                        section_id=cross_listed_section_id,
                        template_type=template_type,
                        term_id=term_id,
                    )

        return True

    def ping(self):
        with SMTP(self.bcop_smtp_server, port=self.bcop_smtp_port) as smtp:
            smtp.noop()
            return True

    @classmethod
    def get_email_addresses(cls, user):
        if app.config['EMAIL_TEST_MODE']:
            config_value = app.config['EMAIL_REDIRECT_WHEN_TESTING']
            return config_value if isinstance(config_value, list) else [config_value]
        else:
            email = user.get('email')
            return [email] if email and email.strip() else []


def write_email_to_log(message, recipient, subject_line):
    app.logger.info(f"""

        To: {recipient['name']} <{recipient['email']}>
        Cc: Course Capture Admin <{app.config['EMAIL_DIABLO_ADMIN']}>
        From: {app.config['EMAIL_COURSE_CAPTURE_SUPPORT_LABEL']} <{app.config['EMAIL_COURSE_CAPTURE_SUPPORT']}>
        Subject: {subject_line}

        Message:
        {message}

    """)
