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
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait

from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class CoursesPage(DiabloPages):

    def load_instructor_homepage(self):
        app.logger.info('Loading instructor homepage')
        self.driver.get(f"{app.config['BASE_URL']}/home")

    COURSE_ROW = (By.XPATH, '//a[contains(@id, "link-course-")]')

    # COURSES

    @staticmethod
    def course_row_locator(section):
        return By.XPATH, f'//tr[contains(., "{section.code}") and contains(., "{section.ccn}")]'

    @staticmethod
    def course_row_link_locator(section):
        return By.ID, f'link-course-{section.ccn}'

    def wait_for_course_results(self):
        Wait(self.driver, util.get_short_timeout()).until(
            ec.visibility_of_any_elements_located(self.COURSE_ROW),
        )

    def course_row_link(self, section):
        return self.element((self.course_row_link_locator(section)))

    def click_course_page_link(self, section):
        app.logger.info(f'Clicking the link to the course page for {section.code}')
        self.wait_for_page_and_click((By.ID, f'link-course-{section.ccn}'))

    # OPT-IN SETTINGS

    OPT_IN_BY_DEFAULT_RADIO = By.ID, 'all-future-courses-opt-in'
    OPT_OUT_BY_DEFAULT_RADIO = By.ID, 'choose-courses-opt-in'
    REMINDER_EMAIL_CBX = By.ID, 'email-checkbox'

    def set_opt_in_by_default(self):
        app.logger.info('Clicking the opt-in-by-default radio')
        self.wait_for_element_and_click(self.OPT_IN_BY_DEFAULT_RADIO)

    def set_opt_out_by_default(self):
        app.logger.info('Clicking the opt-out-by-default radio')
        self.wait_for_element_and_click(self.OPT_OUT_BY_DEFAULT_RADIO)

    def is_instructor_opted_in_by_default(self):
        self.when_present(self.OPT_IN_BY_DEFAULT_RADIO, util.get_short_timeout())
        return self.element(self.OPT_IN_BY_DEFAULT_RADIO).is_selected()

    def receive_email_reminders(self):
        if self.is_email_reminders_checked():
            app.logger.info('Receive email reminders is already checked')
        else:
            app.logger.info('Clicking the email reminders checkbox')
            self.wait_for_element_and_click(self.REMINDER_EMAIL_CBX)

    def decline_email_reminders(self):
        if self.is_email_reminders_checked():
            app.logger.info('Clicking the email reminders checkbox')
            self.wait_for_element_and_click(self.REMINDER_EMAIL_CBX)
        else:
            app.logger.info('Receive email reminders is already unchecked')

    def is_email_reminders_checked(self):
        return self.element(self.REMINDER_EMAIL_CBX).is_selected()

    def is_email_reminders_el_enabled(self):
        return self.element(self.REMINDER_EMAIL_CBX).is_enabled()
