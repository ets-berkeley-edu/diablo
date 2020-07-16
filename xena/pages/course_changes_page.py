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

from datetime import datetime
import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class CourseChangesPage(DiabloPages):

    NO_RESULTS_MSG = (By.XPATH, '//div[contains(text(), "No changes within scheduled courses.")]')

    @staticmethod
    def course_row_xpath(section):
        return f'//tr[contains(., "{section.code}, {section.number}")]'

    @staticmethod
    def meeting_time_format(time_str):
        return datetime.strftime(datetime.strptime(time_str, '%I:%M %p'), '%-I:%M %p')

    @staticmethod
    def meeting_time_str(meeting):
        start = CourseChangesPage.meeting_time_format(meeting.start_time)
        end = CourseChangesPage.meeting_time_format(meeting.end_time)
        return f'{start} - {end}'

    @staticmethod
    def recording_date_str(meeting, term):
        dates = meeting.expected_recording_dates(term)
        start = dates[0].strftime('%Y-%m-%d')
        end = dates[-1].strftime('%Y-%m-%d')
        return f'{start} - {end}'

    def load_page(self):
        app.logger.info('Loading the course changes page')
        self.driver.get(f'{app.config["BASE_URL"]}/changes')

    def is_course_row_present(self, section):
        return self.is_present((By.XPATH, CourseChangesPage.course_container_xpath(section)))

    def wait_for_results(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(CourseChangesPage.PAGE_HEADING))

    def wait_for_course_row(self, section):
        loc = By.XPATH, CourseChangesPage.course_container_xpath(section)
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(loc))
        time.sleep(1)

    @staticmethod
    def course_container_xpath(section):
        return f'//div[contains(@class, "container") and contains(., "Section ID: {section.ccn}")]'

    @staticmethod
    def scheduled_card_xpath(section):
        return f'({CourseChangesPage.course_container_xpath(section)}//div[contains(@class, "v-card")][contains(., "Scheduled")])[1]'

    @staticmethod
    def scheduled_card_detail_xpath(section, heading, node=None):
        i = node or 1
        return f'{CourseChangesPage.scheduled_card_xpath(section)}//h5[contains(., "{heading}")]/following-sibling::div[{i}]'

    def scheduled_card_summary(self, section):
        xpath = f'{CourseChangesPage.scheduled_card_xpath(section)}/div[@class="v-card__subtitle"]'
        return self.element((By.XPATH, xpath)).text.strip()

    def scheduled_card_old_instructors(self, section, node=None):
        xpath = CourseChangesPage.scheduled_card_detail_xpath(section, 'Obsolete Instructors', node)
        return self.element((By.XPATH, xpath)).get_attribute('innerText')

    def scheduled_card_new_instructors(self, section, node=None):
        xpath = CourseChangesPage.scheduled_card_detail_xpath(section, 'Joined course', node)
        return self.element((By.XPATH, xpath)).get_attribute('innerText')

    def scheduled_card_old_room(self, section):
        xpath = CourseChangesPage.scheduled_card_detail_xpath(section, 'Meeting')
        return self.element((By.XPATH, xpath)).get_attribute('innerText')

    def scheduled_card_old_schedule(self, section):
        xpath = CourseChangesPage.scheduled_card_detail_xpath(section, 'Meeting', 2)
        return self.element((By.XPATH, xpath)).get_attribute('innerText')

    @staticmethod
    def current_card_xpath(section):
        return f'({CourseChangesPage.course_container_xpath(section)}//div[contains(@class, "v-card")][contains(., "Current")])[1]'

    @staticmethod
    def current_card_detail_xpath(section, heading, list_node, detail_node):
        detail_node = detail_node or 1
        path_to_el = f'{CourseChangesPage.current_card_xpath(section)}//h5[contains(., "{heading}")]/following-sibling::div'
        return f'{path_to_el}[{list_node}]/div[{detail_node}]' if list_node else f'{path_to_el}[{detail_node}]'

    def current_card_instructors(self, section, node):
        xpath = CourseChangesPage.current_card_detail_xpath(section, 'Instructors', list_node=None, detail_node=node)
        return self.element((By.XPATH, xpath)).get_attribute('innerText')

    def current_card_schedule(self, section, list_node, detail_node):
        xpath = CourseChangesPage.current_card_detail_xpath(section, 'All Meetings', list_node, detail_node)
        return self.element((By.XPATH, xpath)).get_attribute('innerText')
