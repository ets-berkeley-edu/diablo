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

import pytest
from xena.models.async_job import AsyncJob
from xena.models.email import Email
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestInvitations:

    test_data = util.parse_sign_up_test_data()[2]
    section = Section(test_data)

    def test_log_in_admin(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.wait_for_diablo_title('The Ouija Board')

    def test_disable_jobs(self):
        # Clear the queued_emails queue and then shut off all jobs to prevent unexpected additions to the queue
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.QUEUED_EMAILS)
        self.jobs_page.disable_all_jobs()

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    def test_course_auto_invites_run_jobs(self):
        util.reset_invite_test_data(self.term, self.section)
        self.jobs_page.load_page()
        self.jobs_page.run_instructor_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.INSTRUCTOR_EMAILS)
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.QUEUED_EMAILS)

    def test_course_auto_invites_delivered(self):
        # TODO - check for all instructors
        subject = f'{self.term.name} Course Capture - {self.section.code} (To: {self.section.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_delivered(email)

    def test_inst_auto_invite_run_jobs(self):
        util.reset_invite_test_data(self.term, self.section, self.section.instructors[0])
        self.email_page.delete_all_messages()
        self.jobs_page.load_page()
        self.jobs_page.run_instructor_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.INSTRUCTOR_EMAILS)
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.QUEUED_EMAILS)

    def test_inst_auto_invite_delivered(self):
        subject = f'{self.term.name} Course Capture - {self.section.code} (To: {self.section.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_delivered(email)

    def test_course_manual_invite_run_jobs(self):
        self.email_page.delete_all_messages()
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.click_send_invite_button()
        self.jobs_page.load_page()
        self.jobs_page.run_instructor_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.INSTRUCTOR_EMAILS)
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.wait_for_most_recent_job_success(AsyncJob.QUEUED_EMAILS)

    def test_course_manual_invite_delivered(self):
        subject = f'{self.term.name} Course Capture - {self.section.code} (To: {self.section.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_delivered(email)
