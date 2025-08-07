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
import time

from flask import current_app as app
from selenium.webdriver.common.by import By

from xena.pages.page import Page
from xena.test_utils import util


class ICalendarPage(Page):

    VALIDATOR_FORM = (By.ID, 'validate-form')
    VALIDATOR_TEXTAREA = (By.ID, 'jform_ical_text')
    VALIDATOR_SUCCESS_MESSAGE = (By.XPATH, '//div[@id="results"]/div[contains(@class, "alert-success")]')

    def load_validator_page(self):
        app.logger.info('Loading iCalendar validator page')
        self.driver.get('http://icalendar.org/validator.html')

    def validate_file(self, file_path):
        app.logger.info('Validating iCalendar file by entering the text')
        self.scroll_to_element(ICalendarPage.VALIDATOR_TEXTAREA)
        with open(file_path) as ics_file:
            self.wait_for_element_and_type(ICalendarPage.VALIDATOR_TEXTAREA, ics_file.read())
            time.sleep(1)
        self.element(ICalendarPage.VALIDATOR_FORM).submit()
        app.logger.info('Waiting for validator success message')
        self.wait_for_element(ICalendarPage.VALIDATOR_SUCCESS_MESSAGE, util.get_short_timeout())
        self.wait_for_text_in_element(
            ICalendarPage.VALIDATOR_SUCCESS_MESSAGE,
            'Success',
        )
        time.sleep(util.get_click_sleep())
