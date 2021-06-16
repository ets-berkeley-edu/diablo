"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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


class DiabloPages(Page):

    OUIJA_BOARD_LINK = (By.ID, 'sidebar-link-Ouija Board')
    ROOMS_LINK = (By.ID, 'sidebar-link-Rooms')
    COURSE_CHANGES_LINK = (By.ID, 'sidebar-link-Course Changes')

    MENU_BUTTON = (By.ID, 'btn-main-menu')
    BLACKOUTS_LINK = (By.ID, 'menu-item-blackouts')
    EMAIL_TEMPLATES_LINK = (By.ID, 'menu-item-email-templates')
    JOBS_LINK = (By.ID, 'menu-item-jobs')
    JOB_HISTORY_LINK = (By.ID, 'menu-item-job-history')
    LOG_OUT_LINK = (By.ID, 'menu-item-log-out')

    SPINNER = (By.XPATH, '//div[contains(@class, "spinner")]')
    ALERT_MSG = (By.ID, 'alert-text')
    ERROR_REDIRECT = (By.XPATH, '//span[text()="Request failed with status code 504"]')
    VISIBLE_MENU_OPTION = (By.XPATH, '//div[contains(@class, "menuable__content__active")]//span[contains(@id, "-option-")]')

    @staticmethod
    def menu_option_locator(option_str):
        return By.XPATH, f'//div[@role="option"][contains(., "{option_str}")]'

    def wait_for_diablo_title(self, string):
        self.wait_for_title(f'{string} | Course Capture')

    def click_ouija_board_link(self):
        app.logger.info('Clicking Ouija Board link')
        self.wait_for_element_and_click(DiabloPages.OUIJA_BOARD_LINK)

    def click_rooms_link(self):
        app.logger.info('Clicking Rooms link')
        self.wait_for_element_and_click(DiabloPages.ROOMS_LINK)

    def click_course_changes_link(self):
        app.logger.info('Clicking Course Changes link')
        self.wait_for_element_and_click(DiabloPages.COURSE_CHANGES_LINK)

    def click_menu_button(self):
        self.wait_for_element_and_click(DiabloPages.MENU_BUTTON)

    def open_menu(self):
        if not self.is_present(DiabloPages.LOG_OUT_LINK) or not self.element(DiabloPages.LOG_OUT_LINK).is_displayed():
            app.logger.info('Clicking header menu button')
            self.click_menu_button()

    def click_blackouts_link(self):
        app.logger.info('Clicking Blackouts link')
        self.open_menu()
        self.wait_for_page_and_click(DiabloPages.BLACKOUTS_LINK)

    def click_email_templates_link(self):
        app.logger.info('Clicking Email Templates link')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.EMAIL_TEMPLATES_LINK)

    def click_jobs_link(self):
        app.logger.info("Clicking 'The Engine Room' link")
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.JOBS_LINK)

    def click_job_history_link(self):
        app.logger.info('Clicking Job History link')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.JOB_HISTORY_LINK)

    def log_out(self):
        app.logger.info('Logging out')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.LOG_OUT_LINK)
        # Logging out is not working the first time in some cases, retry for now
        time.sleep(2)
        if self.is_present(DiabloPages.LOG_OUT_LINK):
            self.open_menu()
            self.wait_for_element_and_click(DiabloPages.LOG_OUT_LINK)

    def click_menu_option(self, option_text):
        app.logger.info(f"Clicking the option '{option_text}'")
        self.wait_for_element_and_click(DiabloPages.menu_option_locator(option_text))

    def is_menu_option_disabled(self, option_text):
        return self.element(DiabloPages.menu_option_locator(option_text)).get_attribute('aria-disabled') == 'true'

    def visible_menu_options(self):
        Wait(self.driver, app.config['TIMEOUT_SHORT']).until(
            method=ec.visibility_of_any_elements_located(DiabloPages.VISIBLE_MENU_OPTION),
            message=f'Failed visible_menu_options: {DiabloPages.VISIBLE_MENU_OPTION}',
        )
        return [el.text for el in self.elements(DiabloPages.VISIBLE_MENU_OPTION)]

    # COURSE ROWS

    @staticmethod
    def course_opt_out_button_locator(section):
        return By.ID, f'toggle-opt-out-{section.ccn}'

    @staticmethod
    def course_opt_out_button_clickable_locator(section):
        return By.XPATH, f'//input[@id="toggle-opt-out-{section.ccn}"]/following-sibling::div'

    def toggle_course_opt_out(self, section):
        app.logger.info(f'Clicking the opt-out button for {section.code}')
        self.element(DiabloPages.course_opt_out_button_clickable_locator(section)).click()

    def is_course_opted_out(self, section):
        if self.element(DiabloPages.course_opt_out_button_locator(section)).get_attribute('aria-checked') == 'true':
            return True
        else:
            return False

    def set_course_opt_out(self, section):
        if self.is_course_opted_out(section):
            app.logger.info('Course is already opted out')
        else:
            self.toggle_course_opt_out(section)

    def set_course_opt_in(self, section):
        if self.is_course_opted_out(section):
            self.toggle_course_opt_out(section)
        else:
            app.logger.info('Course is already opted in')

    # 404 PAGE

    def wait_for_404(self):
        Wait(self.driver, util.get_medium_timeout()).until(ec.url_contains('404'))
