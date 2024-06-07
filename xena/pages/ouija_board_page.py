"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

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

import csv
import glob
import os
import shutil
import time

from flask import current_app as app
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.courses_page import CoursesPage
from xena.test_utils import util


class OuijaBoardPage(CoursesPage):

    DOWNLOAD_CSV_BUTTON = (By.XPATH, '//button[contains(., "Download CSV")]')

    NO_COURSES_MSG = (By.XPATH, '//div[text()=" No courses. "]')

    SEARCH_INPUT = (By.ID, 'input-search')
    SEARCH_SELECT_BUTTON = (By.XPATH, '//div[@aria-haspopup="listbox"]')
    SEARCH_SELECT_SELECTION = (By.XPATH, '//input[@id="ouija-filter-options"]/preceding-sibling::div')
    SEARCH_SELECT_OPTION = (By.XPATH, '//div[@role="listbox"]/div[@role="option"]//div[contains(@class, "title")]')

    FILTER_ALL_OPTION = (By.XPATH, '//div[@role="option"][contains(., "All")]')
    FILTER_OPTED_OUT = (By.XPATH, '//div[@role="option"][contains(., "Opted Out")]')
    FILTER_SCHEDULED_OPTION = (By.XPATH, '//div[@role="option"][contains(., "Scheduled") and not(contains(., "Nonstandard"))]')
    FILTER_NO_INSTRUCTORS_OPTION = (By.XPATH, '//div[@role="option"][contains(., "No Instructors")]')

    NO_RESULTS_MSG = (By.ID, 'message-when-zero-courses')

    def hit_url(self):
        self.driver.get(f'{app.config["BASE_URL"]}/ouija')

    def load_page(self):
        app.logger.info('Loading the Ouija Board')
        self.hit_url()
        self.wait_for_ouija_title()

    def load_instructor_view(self):
        app.logger.info('Loading the instructor home page')
        self.driver.get(f'{app.config["BASE_URL"]}/home')

    def wait_for_ouija_title(self):
        self.wait_for_diablo_title('Ouija Board')

    def download_csv_and_get_section_ids(self):
        app.logger.info(f'Downloading course CSV to {util.default_download_dir()}')

        # Make sure a clean download directory exists
        if os.path.isdir(util.default_download_dir()):
            shutil.rmtree(util.default_download_dir())
        os.mkdir(util.default_download_dir())

        # Click the download button and wait for the download to complete
        self.wait_for_page_and_click(OuijaBoardPage.DOWNLOAD_CSV_BUTTON)
        tries = 0
        max_tries = 15
        while tries <= max_tries:
            tries += 1
            try:
                assert len(glob.glob(f'{util.default_download_dir()}/*.csv')) == 1
                break
            except AssertionError:
                if tries == max_tries:
                    raise
                else:
                    time.sleep(1)

        # Parse the section ids from the file
        file = glob.glob(f'{util.default_download_dir()}/*.csv')[0]
        section_ids = []
        with open(file) as csv_file:
            for row in csv.DictReader(csv_file):
                section_ids.append(row['Section Id'])
        section_ids.sort()
        app.logger.info(f'{section_ids}')
        return section_ids

    # SEARCH AND FILTER

    @staticmethod
    def search_courses_option_xpath(status):
        return f'//div[@role="listbox"]/div[@role="option"]//div[contains(@class, "title")][text()="{status}"]'

    def search_for_string(self, string, status):
        app.logger.info(f'Searching courses for {string} with status {status}')
        self.wait_for_element_and_type(OuijaBoardPage.SEARCH_INPUT, string)
        self.wait_for_element_and_click(OuijaBoardPage.SEARCH_SELECT_BUTTON)
        self.wait_for_element_and_click((By.XPATH, self.search_courses_option_xpath(status)))

    def search_for_course_code(self, section):
        app.logger.info(f'Searching for course code {section.code}')
        self.wait_for_element_and_type(OuijaBoardPage.SEARCH_INPUT, section.code)
        time.sleep(1)

    def filter_for_option(self, opt_locator):
        if not self.is_present(opt_locator) or not self.element(opt_locator).is_displayed():
            self.wait_for_element_and_click(OuijaBoardPage.SEARCH_SELECT_BUTTON)
        self.wait_for_page_and_click(opt_locator)
        time.sleep(2)
        self.wait_for_filter_search()

    def wait_for_filter_search(self):
        tries = 0
        retries = 30
        while tries <= retries:
            tries += 1
            try:
                if self.is_present(OuijaBoardPage.COURSE_ROW):
                    app.logger.info('Found course results')
                    break
                else:
                    app.logger.info('Found no course results, checking for the no-results message')
                    Wait(self.driver, 1).until(ec.visibility_of_element_located(OuijaBoardPage.NO_RESULTS_MSG))
                    break
            except TimeoutException:
                if tries == retries:
                    raise
                else:
                    time.sleep(1)
        time.sleep(1)

    def is_course_in_results(self, section):
        return self.is_present(OuijaBoardPage.course_row_locator(section))

    def filter_for_all(self):
        app.logger.info('Filtering by option All')
        self.filter_for_option(OuijaBoardPage.FILTER_ALL_OPTION)

    def filter_for_opted_out(self):
        app.logger.info('Filtering by option Opted Out')
        self.filter_for_option(OuijaBoardPage.FILTER_OPTED_OUT)

    def filter_for_scheduled(self):
        app.logger.info('Filtering by option Scheduled')
        self.filter_for_option(OuijaBoardPage.FILTER_SCHEDULED_OPTION)

    def filter_for_no_instructors(self):
        app.logger.info('Filtering by option Scheduled (Nonstandard Dates)')
        self.filter_for_option(OuijaBoardPage.FILTER_NO_INSTRUCTORS_OPTION)

    # COURSES

    def wait_for_course_result(self, section):
        Wait(self.driver, util.get_short_timeout()).until(
            ec.visibility_of_element_located(self.course_row_locator(section)),
        )

    def course_row_code_el(self, section):
        return self.element((By.XPATH, f'//tr[contains(., "{section.code}")]/td[1]'))

    def course_row_title_el(self, section):
        return self.element((By.XPATH, f'//tr[contains(., "{section.code}")]/td[2]'))

    def course_row_instructors_el(self, section):
        return self.element((By.XPATH, f'//tr[contains(., "{section.code}")]/td[3]'))

    def course_row_room_el(self, section):
        return self.element((By.XPATH, f'//tr[contains(., "{section.code}")]/td[4]'))

    def course_row_days_el(self, section):
        return self.element((By.XPATH, f'//tr[contains(., "{section.code}")]/td[5]'))

    def course_row_time_el(self, section):
        return self.element((By.XPATH, f'//tr[contains(., "{section.code}")]/td[6]'))

    def course_row_status_el(self, section):
        return self.element((By.ID, f'course-{section.ccn}-status'))

    def course_row_approval_status_el(self, section):
        return self.element((By.ID, f'course-{section.ccn}-approval-status'))

    def course_row_sched_status_el(self, section):
        return self.element((By.ID, f'course-{section.ccn}-scheduling-status'))
