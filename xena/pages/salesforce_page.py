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

from config import xena
from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.page import Page
from xena.test_utils import util


class SalesforcePage(Page):

    USERNAME_INPUT = (By.ID, 'username')
    PASSWORD_INPUT = (By.ID, 'password')
    LOG_IN_BUTTON = (By.ID, 'Login')
    SEARCH_INPUT = (By.XPATH, '//input[contains(@title, "Search ")]')

    @staticmethod
    def data_link_xpath():
        return '/../following-sibling::div//a'

    @staticmethod
    def data_number_xpath():
        return '/../following-sibling::div//lightning-formatted-number'

    @staticmethod
    def data_text_field_xpath():
        return '/../following-sibling::div//lightning-formatted-text'

    def data_el_exists(self, xpath):
        Wait(self.driver, 1).until(ec.presence_of_element_located((By.XPATH, xpath)))
        return True

    def course_name_xpath(self, name):
        return f'//span[text()="Project Name"]{self.data_text_field_xpath()}[text()="{name}"]'

    def parent_project_xpath(self, project):
        return f'//span[text()="Parent Project"]{self.data_link_xpath()}[text()="{project}"]'

    def course_id_xpath(self, course_id):
        return f'//span[text()="CourseOfferingID"]{self.data_text_field_xpath()}[text()="{course_id}"]'

    def project_end_date_xpath(self, date):
        return f'//span[text()="Project End Date"]{self.data_text_field_xpath()}[text()="{date}"]'

    def cross_listings_xpath(self, listings):
        return f'//span[text()="Cross-listings"]{self.data_text_field_xpath()}[text()="{listings}"]'

    def num_instructors_xpath(self, num):
        return f'//span[text()="# of Instructors"]{self.data_number_xpath()}[text()="{num}"]'

    def instructor_one_xpath(self, name):
        return f'//span[text()="Instructor 1"]{self.data_link_xpath()}[text()="{name}"]'

    def instructor_two_xpath(self, name):
        return f'//span[text()="Instructor 2"]{self.data_link_xpath()}[text()="{name}"]'

    def instructor_three_xpath(self, name):
        return f'//span[text()="Instructor 3"]{self.data_link_xpath()}[text()="{name}"]'

    def schedule_days_xpath(self, days):
        return f'//span[text()="Schedule Days"]{self.data_text_field_xpath()}[text()="{days}"]'

    def start_time_xpath(self, time):
        return f'//span[text()="Start Time"]{self.data_text_field_xpath()}[text()="{time}"]'

    def end_time_xpath(self, time):
        return f'//span[text()="End Time"]{self.data_text_field_xpath()}[text()="{time}"]'

    def room_xpath(self, room):
        return f'//span[text()="Room"]{self.data_link_xpath()}[text()="{room}"]'

    def sign_up_link_xpath(self, href):
        return f'//span[text()="Sign Up Form Link"]{self.data_link_xpath()}[@href="{href}"]'

    def ccn_xpath(self, ccn):
        return f'//span[text()="CCN"]{self.data_text_field_xpath()}[text()="{ccn}"]'

    def section_xpath(self, section):
        return f'//span[text()="Section"]{self.data_text_field_xpath()}[text()="{section}"]'

    def semester_xpath(self, semester):
        return f'//span[text()="Semester"]{self.data_text_field_xpath()}[text()="{semester}"]'

    def course_title_xpath(self, title):
        return f'//span[text()="Course Title"]{self.data_text_field_xpath()}[text()="{title}"]'

    def log_in(self):
        app.logger.info(f'Logging in to Salesforce')
        self.driver.get(xena.SALESFORCE_BASE_URL)
        self.wait_for_element_and_type(SalesforcePage.USERNAME_INPUT, app.config['SALESFORCE_USERNAME'])
        self.wait_for_element_and_type(SalesforcePage.PASSWORD_INPUT, app.config['SALESFORCE_PASSWORD'])
        self.wait_for_element_and_click(SalesforcePage.LOG_IN_BUTTON)

    def search_for_project(self, ccn):
        app.logger.info(f'Searching for course ID {ccn}')
        self.wait_for_element_and_type_js(SalesforcePage.SEARCH_INPUT, ccn, xena.SALESFORCE_PAUSE)
        self.hit_enter()

    def click_project_result_link(self, project_name):
        app.logger.info(f'Clicking the link to project "{project_name}"')
        self.wait_for_page_and_click_js((By.XPATH, f'//a[contains(text(), "{project_name}")]'), xena.SALESFORCE_PAUSE)
        self.wait_for_element((By.XPATH, self.course_name_xpath(project_name)), util.get_long_timeout())
        time.sleep(1)
