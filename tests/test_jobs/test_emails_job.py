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
from diablo import std_commit
from diablo.jobs.emails_job import EmailsJob
from diablo.lib.util import utc_now
from diablo.models.queued_email import QueuedEmail
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.util import simply_yield


class TestEmailsJob:

    def test_no_email_queued(self):
        """Do nothing if 'queued_emails' table is empty."""
        term_id = app.config['CURRENT_TERM_ID']
        EmailsJob(simply_yield).run()
        std_commit(allow_test_environment=True)
        # Verify that the next job run will have zero queued emails.
        assert len(QueuedEmail.get_all(term_id=term_id)) == 0

        EmailsJob(simply_yield).run()
        std_commit(allow_test_environment=True)
        # If we reach this point then no error occurred.

    def test_send_course_emails(self):
        """Send all email in 'queued_emails' table."""
        term_id = app.config['CURRENT_TERM_ID']
        courses = SisSection.get_courses(section_ids=[50000, 50001], term_id=term_id)
        email_template_type = 'semester_start'

        for course in courses:
            for instructor in course['instructors']:
                QueuedEmail.create(course['sectionId'], email_template_type, term_id, recipient=instructor)
            std_commit(allow_test_environment=True)

        def _get_emails_to_courses():
            emails_sent = []
            for c in courses:
                emails_sent.extend(
                    _get_emails_sent(
                        email_template_type=email_template_type,
                        section_id=c['sectionId'],
                        term_id=term_id,
                    ),
                )
            return emails_sent

        before = utc_now()
        emails_sent_before = _get_emails_to_courses()
        # Run the job
        EmailsJob(simply_yield).run()
        std_commit(allow_test_environment=True)

        # Expect one email per instructor
        emails_sent_after = _get_emails_to_courses()
        assert len(emails_sent_after) == len(emails_sent_before) + 3

        def _find_email(section_id, uid):
            return next((e for e in emails_sent_after if e.section_id == section_id and e.sent_at > before and uid == e.recipient_uid), None)

        for course in courses:
            for instructor in course['instructors']:
                sent_email = _find_email(section_id=course['sectionId'], uid=instructor['uid'])
                assert sent_email
                email_json = sent_email.to_api_json()
                assert email_json['recipientUid'] == instructor['uid']
                assert email_json['sectionId'] == course['sectionId']
                assert email_json['templateType'] == email_template_type
                assert email_json['termId'] == term_id
                assert email_json['sentAt']

    def test_queued_email_for_admin(self):
        """Certain email template types are for admin recipients only."""
        def _emails_sent():
            return _get_emails_sent(email_template_type=email_template_type, section_id=section_id, term_id=term_id)

        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50005
        email_template_type = 'admin_operator_requested'
        recipient_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
        QueuedEmail.create(
            section_id,
            email_template_type,
            term_id,
            recipient={
                'name': 'Course Capture Admin',
                'uid': recipient_uid,
            },
        )
        std_commit(allow_test_environment=True)

        before = utc_now()
        emails_sent_before = _emails_sent()
        # Run the job
        EmailsJob(simply_yield).run()
        std_commit(allow_test_environment=True)

        # Expect email to admin email address
        emails_sent_after = _emails_sent()
        assert len(emails_sent_after) == len(emails_sent_before) + 1

        sent_email = next((e for e in emails_sent_after if e.section_id == section_id and e.sent_at > before), None)
        assert sent_email
        email_json = sent_email.to_api_json()
        assert email_json['recipientUid'] == recipient_uid
        assert email_json['sectionId'] == section_id
        assert email_json['templateType'] == email_template_type
        assert email_json['termId'] == term_id
        assert email_json['sentAt']


def _get_emails_sent(email_template_type, section_id, term_id):
    return SentEmail.get_emails_of_type(
        section_ids=[section_id],
        template_type=email_template_type,
        term_id=term_id,
    )
