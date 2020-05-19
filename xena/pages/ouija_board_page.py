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
from selenium.webdriver.common.by import By
from xena.pages.diablo_pages import DiabloPages


class OuijaBoardPage(DiabloPages):

    SEARCH_INPUT = (By.ID, 'input-search')
    SEARCH_SELECT_BUTTON = (By.XPATH, '//div[@aria-haspopup="listbox"]')
    SEARCH_SELECT_SELECTION = (By.XPATH, '//input[@id="ouija-filter-options"]/preceding-sibling::div')
    SEARCH_SELECT_OPTION = (By.XPATH, '//div[@role="listbox"]/div[@role="option"]//div[contains(@class, "title")]')

    @staticmethod
    def search_courses_option_xpath(self, status):
        return f'//div[@role="listbox"]/div[@role="option"]//div[contains(@class, "title")][text()="{status}"]'

    def load_page(self):
        app.logger.info('Loading the Ouija Board')
        self.driver.get(f'{app.config["BASE_URL"]}/ouija')
        self.wait_for_diablo_title('The Ouija Board')

    def search_courses(self, string, status):
        app.logger.info(f'Searching courses for {string} with status {status}')
        self.wait_for_element_and_type(OuijaBoardPage.SEARCH_INPUT, string)
        self.wait_for_element_and_click(OuijaBoardPage.SEARCH_SELECT_BUTTON)
        self.wait_for_element_and_click((By.XPATH, self.search_courses_option_xpath(status)))

    def course_row_link(self, section):
        return self.element((By.ID, f'link-course-{section.ccn}'))

    def course_row_code_el(self, section):
        return self.element((By.XPATH, f'//tr[@id="{section.ccn}"]/td[2]'))

    def course_row_title_el(self, section):
        return self.element((By.XPATH, f'//tr[@id="{section.ccn}"]/td[3]'))

    def course_row_instructors_el(self, section):
        return self.element((By.XPATH, f'//tr[@id="{section.ccn}"]/td[4]'))

    def course_row_room_el(self, section):
        return self.element((By.XPATH, f'//tr[@id="{section.ccn}"]/td[5]'))

    def course_row_days_el(self, section):
        return self.element((By.XPATH, f'//tr[@id="{section.ccn}"]/td[6]'))

    def course_row_time_el(self, section):
        return self.element((By.XPATH, f'//tr[@id="{section.ccn}"]/td[7]'))

    def click_sign_up_page_link(self, section):
        app.logger.info(f'Clicking the link to the sign up page for {section.code}')
        self.wait_for_page_and_click((By.ID, f'link-course-{section.ccn}'))
