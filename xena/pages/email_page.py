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

import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.page import Page
from xena.test_utils import util


class EmailPage(Page):

    USERNAME_INPUT = (By.ID, 'login-username')
    NEXT_BUTTON = (By.ID, 'login-signin')
    PASSWORD_INPUT = (By.ID, 'login-passwd')
    LOG_OUT_LINK = (By.ID, 'profile-signout-link')
    COMPOSE_BUTTON = (By.LINK_TEXT, 'Compose')
    SELECT_ALL_CBX = (By.XPATH, '//button[@data-test-id="checkbox"]')
    DELETE_BUTTON = (By.XPATH, '//button[@data-test-id="toolbar-delete"]')
    MESSAGE_ROW = (By.XPATH, '//a[@data-test-id="message-list-item"]')
    EMPTY_FOLDER = (By.XPATH, '//span[contains(., " folder is empty")]')

    @staticmethod
    def message_locator(message):
        return By.XPATH, f'//span[contains(@title, "{message.subject}")]/ancestor::a'

    def message_row(self, message):
        return self.element(EmailPage.message_locator(message))

    def load_page(self):
        app.logger.info('Loading email')
        self.driver.get('https://mail.yahoo.com')
        self.wait_for_element(EmailPage.COMPOSE_BUTTON, util.get_short_timeout())
        # Pause then hit escape to dismiss any modals that appear
        time.sleep(1)
        self.hit_escape()

    def log_in(self):
        app.logger.info('Logging in to email')
        self.driver.get('https://login.yahoo.com')
        self.wait_for_element_and_type_js('login-username', app.config['XENA_EMAIL_USERNAME'])
        self.click_element_js(EmailPage.NEXT_BUTTON, 2)
        self.wait_for_element_and_type_js('login-passwd', app.config['XENA_EMAIL_PASSWORD'])
        self.click_element_js(EmailPage.NEXT_BUTTON, 2)
        Wait(self.driver, util.get_short_timeout()).until(ec.presence_of_element_located(EmailPage.LOG_OUT_LINK))
        time.sleep(1)

    def is_message_present(self, message):
        return self.is_present(EmailPage.message_locator(message))

    def is_message_delivered(self, message):
        app.logger.info(f'Waiting for email subject {message.subject}')
        self.load_page()
        tries = 0
        retries = app.config['XENA_EMAIL_DELIVERY_RETRIES']
        while tries <= retries:
            tries += 1
            try:
                app.logger.info(f'Attempt {tries}')
                assert self.is_message_present(message)
                return True
            except Exception as e:
                app.logger.info(f'Error: {e}, scrolling down')
                self.scroll_to_bottom()
                time.sleep(util.get_short_timeout())
                if tries == retries:
                    return False

    def open_message(self, message):
        app.logger.info(f'Opening email with subject {message.subject}')
        self.wait_for_element_and_click(EmailPage.message_locator(message))
        time.sleep(10)

    def delete_all_messages(self):
        self.load_page()
        if self.elements(EmailPage.MESSAGE_ROW):
            app.logger.info('Deleting all messages')
            self.wait_for_page_and_click_js(EmailPage.SELECT_ALL_CBX, 2)
            self.wait_for_page_and_click_js(EmailPage.DELETE_BUTTON, 2)
            Wait(self.driver, util.get_long_timeout()).until(ec.invisibility_of_element_located(EmailPage.MESSAGE_ROW))
        elif self.is_present(EmailPage.EMPTY_FOLDER):
            app.logger.info('There are no messages to delete')
        else:
            app.logger.warning('Unable to tell if there are messages in the inbox')
