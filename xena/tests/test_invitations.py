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
from xena.models.email import Email
from xena.models.section import Section
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestInvitations:

    section_1 = Section(util.parse_course_test_data()[4])
    section_2 = Section(util.parse_course_test_data()[5])

    def test_log_in_admin(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.wait_for_ouija_title()

    def test_disable_jobs(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    def test_course_opt_out(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section_2)
        self.ouija_page.filter_for_all()
        self.ouija_page.wait_for_course_result(self.section_2)
        self.ouija_page.set_course_opt_out(self.section_2)

    def test_course_auto_invites_run_jobs(self):
        util.reset_invite_test_data(self.term, self.section_1)
        util.reset_invite_test_data(self.term, self.section_2)
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()

    def test_course_auto_invites_delivered(self):
        subject = f'Invitation {self.section_1.term.name} {self.section_1.code} (To: {self.section_1.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_delivered(email) is True

    def test_course_auto_invites_not_delivered(self):
        subject = f'Invitation {self.section_2.term.name} {self.section_2.code} (To: {self.section_2.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_present(email) is False

    def test_inst_auto_invite_run_jobs(self):
        util.reset_invite_test_data(self.term, self.section_1, self.section_1.instructors[0])
        self.email_page.delete_all_messages()
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()

    def test_inst_auto_invite_delivered(self):
        subject = f'Invitation {self.section_1.term.name} {self.section_1.code} (To: {self.section_1.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_delivered(email)

    def test_course_manual_invite_send(self):
        self.email_page.delete_all_messages()
        self.sign_up_page.load_page(self.section_1)
        self.sign_up_page.click_send_invite_button()

    def test_course_opt_out_no_invite_button(self):
        self.sign_up_page.load_page(self.section_2)
        self.sign_up_page.wait_for_element(SignUpPage.OPTED_OUT, util.get_short_timeout())
        assert self.sign_up_page.visible_opt_out() == 'Opted out'
        assert self.sign_up_page.is_present(SignUpPage.SEND_INVITE_BUTTON) is False

    def test_course_opt_in(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section_2)
        self.ouija_page.filter_for_all()
        self.ouija_page.wait_for_course_result(self.section_2)
        self.ouija_page.set_course_opt_in(self.section_2)

    def test_course_opt_in_invite_button(self):
        self.sign_up_page.load_page(self.section_2)
        self.sign_up_page.wait_for_element(SignUpPage.SEND_INVITE_BUTTON, util.get_short_timeout())
        assert self.sign_up_page.is_present(SignUpPage.OPTED_OUT) is False

    def test_course_manual_invite_run_jobs(self):
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()

    def test_course_manual_invite_delivered(self):
        subject = f'Invitation {self.section_1.term.name} {self.section_1.code} (To: {self.section_1.instructors[0].email})'
        email = Email(msg_type=None, sender=None, subject=subject)
        assert self.email_page.is_message_delivered(email) is True
