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
from diablo.jobs.kaltura_job import KalturaJob
from diablo.jobs.tasks.queued_emails_task import QueuedEmailsTask
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.util import simply_yield, test_approvals_workflow


class TestKalturaJob:

    def test_new_course_scheduled(self):
        """New courses are scheduled for recording by default."""
        with test_approvals_workflow(app):
            section_id = 50012
            term_id = app.config['CURRENT_TERM_ID']
            course = SisSection.get_course(section_id=section_id, term_id=term_id)
            instructors = course['instructors']
            assert len(instructors) == 2

            # Verify that course is not scheduled
            assert Scheduled.get_scheduled(section_id=section_id, term_id=term_id) is None

            def _get_emails_sent():
                return SentEmail.get_emails_of_type(
                    section_ids=[section_id],
                    template_type='new_class_scheduled',
                    term_id=term_id,
                )

            """If a course is scheduled for recording then email is sent to its instructor(s)."""
            email_count = len(_get_emails_sent())
            KalturaJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            assert Scheduled.get_scheduled(section_id=section_id, term_id=term_id)

            # Verify emails sent
            QueuedEmailsTask().run()
            emails_sent = _get_emails_sent()
            assert len(emails_sent) == email_count + 2
            assert [emails_sent[-1].recipient_uid, emails_sent[-2].recipient_uid] == ['10009', '10010']
            email_sent = emails_sent[-1]
            assert email_sent.section_id == section_id
            assert email_sent.template_type == 'new_class_scheduled'
            assert email_sent.term_id == term_id

            """If recordings were already scheduled then do nothing, send no email."""
            email_count = len(_get_emails_sent())
            KalturaJob(simply_yield).run()
            assert len(_get_emails_sent()) == email_count
