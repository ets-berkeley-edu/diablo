"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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

from diablo import std_commit
from diablo.jobs.emails_job import EmailsJob
from diablo.jobs.remind_instructors_partially_approved_job import RemindInstructorsPartiallyApprovedJob
from diablo.jobs.semester_start_job import SemesterStartJob
from diablo.models.opt_in import OptIn
from diablo.models.queued_email import QueuedEmail
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from tests.util import simply_yield, test_scheduling_workflow


class TestRemindInstructorsPartiallyApprovedJob:

    def test_remind_instructors_scheduled(self):
        """Eligible, opted-in courses are scheduled for recording and get reminder emails."""
        with test_scheduling_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            instructor_uid = '10008'
            solo_taught_section_id = '50007'
            co_taught_section_id = '50010'

            OptIn.update_opt_in(instructor_uid=instructor_uid, term_id=term_id, section_id=solo_taught_section_id, opt_in=True)
            OptIn.update_opt_in(instructor_uid=instructor_uid, term_id=term_id, section_id=co_taught_section_id, opt_in=True)
            std_commit(allow_test_environment=True)

            emails_to_instructor_count = len(SentEmail.get_emails_sent_to(instructor_uid))
            SemesterStartJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            RemindInstructorsPartiallyApprovedJob(simply_yield).run()
            std_commit(allow_test_environment=True)

            scheduled = Scheduled.get_scheduled(section_id=solo_taught_section_id, term_id=term_id)
            assert instructor_uid in scheduled.instructor_uids

            assert not Scheduled.get_scheduled(section_id=co_taught_section_id, term_id=term_id)

            # Verify one reminder sent to each instructor, even in the case of multiple eligible courses.
            reminders_queued_for_instructor = []
            for e in QueuedEmail.get_all(term_id=term_id):
                if e.recipient['uid'] == instructor_uid and e.template_type == 'remind_partially_approved':
                    reminders_queued_for_instructor.append(e)

            assert len(reminders_queued_for_instructor) == 1
            assert reminders_queued_for_instructor[0].message == 'You are partially approved, William Kinderman!\n'\
                'MATH C51, LEC 001 | STAT C51, LEC 003: Linear algebra and differential calculus'

            EmailsJob(simply_yield).run()
            emails_sent = SentEmail.get_emails_sent_to(instructor_uid)
            assert len(emails_sent) > emails_to_instructor_count
            email_sent = emails_sent[-1]
            assert email_sent.template_type == 'remind_partially_approved'
            assert email_sent.term_id == term_id
