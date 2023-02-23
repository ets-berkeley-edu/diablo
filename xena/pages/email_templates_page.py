"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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

import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class EmailTemplatesPage(DiabloPages):
    TEMPLATE_TYPE_SELECT = (By.XPATH, '//input[@id="select-email-template-type"]/..')
    TEMPLATE_NAME_INPUT = (By.XPATH, '//input[@id="input-template-name"]')
    TEMPLATE_SUBJECT_INPUT = (By.XPATH, '//input[@id="input-template-subject-line"]')
    CODE_BUTTON = (By.XPATH, '//button[contains(., "code")]')
    TEMPLATE_BODY_INPUT = (By.XPATH, '//div[@contenteditable="true"]')
    CODES_BUTTON = (By.ID, 'btn-email-template-codes')
    CODES_DIV = (By.XPATH, '//div[contains(text(), "Template Codes")]/following-sibling::div[1]')
    CODES_CLOSE_BUTTON = (By.ID, 'btn-close-template-codes-dialog')
    SAVE_BUTTON = (By.ID, 'save-email-template')
    CANCEL_BUTTON = (By.ID, 'cancel-edit-of-email-template')

    @staticmethod
    def template_codes():
        return [
            'course.aprx', 'course.days', 'course.format', 'course.name', 'course.room', 'course.section', 'course.time.end',
            'course.time.start', 'course.title', 'instructors.all', 'instructors.pending', 'publish.type',
            'publish.type.previous', 'recipient.name', 'recording.type', 'recording.type.previous', 'signup.url',
            'term.name',
        ]

    @staticmethod
    def template_row_xpath(template):
        return f'//tr[contains(., "{template.template_type.value}")]'

    @staticmethod
    def edit_template_link_locator(template):
        return By.XPATH, f'{EmailTemplatesPage.template_row_xpath(template)}//a'

    @staticmethod
    def test_email_button_locator(template):
        return By.XPATH, f'{EmailTemplatesPage.template_row_xpath(template)}//button[contains(@id, "send-test-email")]'

    @staticmethod
    def delete_email_button_locator(template):
        return By.XPATH, f'{EmailTemplatesPage.template_row_xpath(template)}//button[contains(@id, "delete-email-template")]'

    def hit_url(self):
        self.driver.get(f'{app.config["BASE_URL"]}/email/templates')

    def load_page(self):
        app.logger.info('Loading the templates page')
        self.hit_url()

    def wait_for_template_row(self, template):
        Wait(self.driver, util.get_short_timeout()).until(
            ec.visibility_of_element_located(EmailTemplatesPage.edit_template_link_locator(template)),
        )

    def click_template_select(self):
        app.logger.info('Expanding template options')
        self.wait_for_page_and_click(EmailTemplatesPage.TEMPLATE_TYPE_SELECT)

    def enter_template_name(self, name):
        app.logger.info(f'Entering template name "{name}"')
        self.wait_for_element_and_type(EmailTemplatesPage.TEMPLATE_NAME_INPUT, name)

    def enter_subject(self, subject):
        app.logger.info(f'Entering template subject "{subject}"')
        self.wait_for_element_and_type(EmailTemplatesPage.TEMPLATE_SUBJECT_INPUT, subject)

    def enter_body(self, body):
        app.logger.info(f'Entering template body "{body}"')
        self.wait_for_element_and_type(EmailTemplatesPage.TEMPLATE_BODY_INPUT, body)

    def enter_body_code(self, code):
        time.sleep(0.25)
        self.click_element_js(EmailTemplatesPage.CODE_BUTTON)
        time.sleep(0.25)
        self.element(EmailTemplatesPage.TEMPLATE_BODY_INPUT).send_keys(code)
        time.sleep(0.25)
        self.click_element_js(EmailTemplatesPage.CODE_BUTTON)
        time.sleep(0.25)
        self.hit_enter()

    def enter_all_codes_in_body(self):
        codes = EmailTemplatesPage.template_codes()
        self.wait_for_element_and_click(EmailTemplatesPage.TEMPLATE_BODY_INPUT)
        self.element(EmailTemplatesPage.TEMPLATE_BODY_INPUT).send_keys('There is nothing like Lockdown KS ')
        for code in codes:
            self.element(EmailTemplatesPage.TEMPLATE_BODY_INPUT).send_keys(f'{code} ')
            self.enter_body_code(code)

    def click_template_codes_button(self):
        app.logger.info('Clicking template codes button')
        self.wait_for_element_and_click(EmailTemplatesPage.CODES_BUTTON)
        Wait(self.driver, 1).until(ec.visibility_of_element_located(EmailTemplatesPage.CODES_DIV))

    def click_close_template_codes_button(self):
        self.wait_for_element_and_click(EmailTemplatesPage.CODES_CLOSE_BUTTON)

    def click_cancel(self):
        app.logger.info('Clicking cancel')
        Wait(self.driver, util.get_short_timeout()).until(
            ec.presence_of_element_located(EmailTemplatesPage.CANCEL_BUTTON),
        )
        self.click_element_js(EmailTemplatesPage.CANCEL_BUTTON)

    def click_save(self):
        app.logger.info('Clicking save')
        Wait(self.driver, util.get_short_timeout()).until(
            ec.presence_of_element_located(EmailTemplatesPage.SAVE_BUTTON),
        )
        self.click_element_js(EmailTemplatesPage.SAVE_BUTTON)

    def click_edit_template_link(self, template):
        app.logger.info(f'Clicking link to edit template type "{template.template_type.value}"')
        self.wait_for_page_and_click_js(
            EmailTemplatesPage.edit_template_link_locator(template), util.get_short_timeout(),
        )

    def click_send_test_email(self, template):
        app.logger.info(f'Clicking test email button for template type "{template.template_type.value}"')
        self.wait_for_page_and_click_js(EmailTemplatesPage.test_email_button_locator(template))

    def click_delete_template_button(self, template):
        app.logger.info(f'Clicking delete button for template type "{template.template_type.value}"')
        self.wait_for_page_and_click_js(EmailTemplatesPage.delete_email_button_locator(template))
        time.sleep(1)

    def create_template(self, template):
        app.logger.info(f'Creating a template of type "{template.template_type.value}"')
        self.load_page()
        self.click_template_select()
        self.click_menu_option(template.template_type.value)
        self.enter_template_name(template.template_type.value)
        self.enter_subject(template.subject)
        self.enter_all_codes_in_body()
        self.click_save()
        self.wait_for_template_row(template)
