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
from diablo import std_commit
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.lib.util import utc_now
from diablo.models.course_preference import CoursePreference
from diablo.models.queued_email import QueuedEmail
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app


class TestQueuedEmailsJob:

    def test_no_email_queued(self):
        """Do nothing if 'queued_emails' table is empty."""
        term_id = app.config['CURRENT_TERM_ID']
        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)
        # Verify that the next job run will have zero queued emails.
        assert len(QueuedEmail.get_all(term_id=term_id)) == 0

        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)
        # If we reach this point then no error occurred.

    def test_send_invitation_emails(self):
        """Send all email in 'queued_emails' table."""
        term_id = app.config['CURRENT_TERM_ID']
        courses = SisSection.get_courses(section_ids=[50000, 50001], term_id=term_id)
        email_template_type = 'invitation'

        for course in courses:
            QueuedEmail.create(course['sectionId'], email_template_type, term_id)
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
        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)

        # Expect one email per instructor
        emails_sent_after = _get_emails_to_courses()
        assert len(emails_sent_after) == len(emails_sent_before) + 2

        def _find_email(section_id):
            return next((e for e in emails_sent_after if e.section_id == section_id and e.sent_at > before), None)

        for course in courses:
            sent_email = _find_email(section_id=course['sectionId'])
            assert sent_email
            email_json = sent_email.to_api_json()
            assert len(email_json['recipientUids'])
            assert set(email_json['recipientUids']) == set([i['uid'] for i in course['instructors']])
            assert email_json['sectionId'] == course['sectionId']
            assert email_json['templateType'] == email_template_type
            assert email_json['termId'] == term_id
            assert email_json['sentAt']

    def test_course_has_opted_out(self):
        """Do not send email to courses that have opted out."""
        def _emails_sent():
            return _get_emails_sent(email_template_type=email_template_type, section_id=section_id, term_id=term_id)

        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50000
        CoursePreference.update_opt_out(term_id=term_id, section_id=section_id, opt_out=True)
        email_template_type = 'invitation'

        QueuedEmail.create(section_id, email_template_type, term_id)
        std_commit(allow_test_environment=True)

        before = utc_now()
        emails_sent_before = _emails_sent()
        # Run the job
        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)

        # Expect no emails sent
        emails_sent_after = _emails_sent()
        assert len(emails_sent_after) == len(emails_sent_before)
        assert not next((e for e in emails_sent_after if e.section_id == section_id and e.sent_at > before), None)

    def test_queued_email_for_admin(self):
        """Certain email template types are for admin recipients only."""
        def _emails_sent():
            return _get_emails_sent(email_template_type=email_template_type, section_id=section_id, term_id=term_id)

        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50005
        email_template_type = 'admin_alert_room_change'

        QueuedEmail.create(section_id, email_template_type, term_id)
        std_commit(allow_test_environment=True)

        before = utc_now()
        emails_sent_before = _emails_sent()
        # Run the job
        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)

        # Expect email to admin email address
        emails_sent_after = _emails_sent()
        assert len(emails_sent_after) == len(emails_sent_before) + 1

        sent_email = next((e for e in emails_sent_after if e.section_id == section_id and e.sent_at > before), None)
        assert sent_email
        email_json = sent_email.to_api_json()
        assert email_json['recipientUids'] == [app.config['EMAIL_DIABLO_ADMIN_UID']]
        assert email_json['sectionId'] == section_id
        assert email_json['templateType'] == email_template_type
        assert email_json['termId'] == term_id
        assert email_json['sentAt']

    def test_currently_no_person_teaching_course(self):
        """If course does not have a proper instructor then the email remains queued."""
        def _emails_sent():
            return _get_emails_sent(email_template_type=email_template_type, section_id=section_id, term_id=term_id)

        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50006
        email_template_type = 'invitation'
        # Courses with no proper instructor are excluded from query results.
        assert not SisSection.get_course(term_id=term_id, section_id=section_id)

        queued_email = QueuedEmail.create(section_id, email_template_type, term_id)
        std_commit(allow_test_environment=True)

        emails_sent_before = _emails_sent()
        # Run the job
        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)

        # Expect no email sent
        emails_sent_after = _emails_sent()
        assert len(emails_sent_after) == len(emails_sent_before)
        # Assert that email is still queued
        assert section_id in QueuedEmail.get_all_section_ids(template_type=email_template_type, term_id=term_id)
        # Clean up
        QueuedEmail.delete(queued_email)

    def test_no_email_template_available(self):
        """If email_template is not available then keep related emails in the queue."""
        def _emails_sent():
            return _get_emails_sent(email_template_type=email_template_type, section_id=section_id, term_id=term_id)

        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50005
        email_template_type = 'waiting_for_approval'

        queued_email = QueuedEmail.create(section_id, email_template_type, term_id)
        std_commit(allow_test_environment=True)

        emails_sent_before = _emails_sent()
        # Run the job
        QueuedEmailsJob(app.app_context).run()
        std_commit(allow_test_environment=True)

        # Expect no email sent
        emails_sent_after = _emails_sent()
        assert len(emails_sent_after) == len(emails_sent_before)
        # Assert that email is still queued
        assert section_id in QueuedEmail.get_all_section_ids(template_type=email_template_type, term_id=term_id)
        # Clean up
        QueuedEmail.delete(queued_email)


def _get_emails_sent(email_template_type, section_id, term_id):
    return SentEmail.get_emails_of_type(
        section_id=section_id,
        template_type=email_template_type,
        term_id=term_id,
    )
