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
import pytest
from selenium.webdriver.common.by import By
from xena.models.email import Email
from xena.models.email_template import EmailTemplate
from xena.models.email_template_type import EmailTemplateType
from xena.models.term import Term
from xena.pages.email_templates_page import EmailTemplatesPage
from xena.test_utils import util

util.reset_email_template_test_data('invitation')


@pytest.mark.usefixtures('page_objects')
class TestEmailTemplates:

    term = Term()
    template = EmailTemplate(
        template_type=EmailTemplateType.INSTR_INVITATION,
        subject='Invitation ',
        body='',
    )

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    def test_log_in(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_email_templates_link()

    def test_template_options(self):
        self.templates_page.click_template_select()
        options = self.templates_page.visible_menu_options()
        types = [templ.value for templ in EmailTemplateType]
        types.sort()
        assert options == types

    def test_create_template_cancel(self):
        self.templates_page.click_menu_option(EmailTemplateType.INSTR_INVITATION.value)
        self.templates_page.click_cancel()

    def test_create_template_name_input(self):
        self.templates_page.click_template_select()
        self.templates_page.click_menu_option(EmailTemplateType.INSTR_INVITATION.value)
        self.templates_page.enter_template_name(self.template)

    def test_create_template_subj_input(self):
        self.templates_page.enter_subject(self.template.subject)
        self.templates_page.element(EmailTemplatesPage.TEMPLATE_SUBJECT_INPUT).send_keys('<code>term.name</code>')
        self.template.subject = f'{self.template.subject}{self.term.name}'

    def test_create_template_show_codes(self):
        self.templates_page.click_template_codes_button()
        for code in EmailTemplatesPage.template_codes():
            assert code in self.templates_page.element(EmailTemplatesPage.CODES_DIV).get_attribute('innerText')

    def test_create_template_enter_codes(self):
        self.templates_page.click_close_template_codes_button()
        self.templates_page.enter_all_codes_in_body()

    def test_create_template_save_template(self):
        self.templates_page.click_save()

    def test_pre_existing_template(self):
        self.templates_page.click_template_select()
        assert self.templates_page.is_menu_option_disabled(self.template.template_type.value)

    def test_edit_template_cancel(self):
        self.templates_page.hit_escape()
        self.templates_page.click_edit_template_link(self.template)
        self.templates_page.click_cancel()

    def test_edit_template_save(self):
        self.templates_page.click_edit_template_link(self.template)
        self.templates_page.click_save()

    def test_email_test_button(self):
        self.templates_page.click_send_test_email(self.template)
        subj = f'{self.template.subject} (To: {app.config["EMAIL_DIABLO_ADMIN"]})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    def test_delete_button(self):
        self.templates_page.load_page()
        self.templates_page.click_delete_template_button(self.template)
        assert not self.templates_page.is_present((By.XPATH, EmailTemplatesPage.template_row_xpath(self.template)))
