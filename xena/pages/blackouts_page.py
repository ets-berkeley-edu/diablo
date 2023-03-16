"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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
import datetime
import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class BlackoutsPage(DiabloPages):
    CREATE_NEW_BUTTON = (By.XPATH, '//button[contains(., "Create New")]')
    NAME_INPUT = (By.ID, 'input-blackout-name')
    CALENDAR_MONTH = (By.XPATH, '//div[@class="vc-title"]')
    CALENDAR_BACK_BUTTON = (By.XPATH, '//div[@class="vc-arrow is-left"]')
    CALENDAR_FORWARD_BUTTON = (By.XPATH, '//div[@class="vc-arrow is-right"]')
    DELETE_BUTTON = (By.XPATH, '//button[contains(@id, "delete-blackout")]')
    SAVE_BUTTON = (By.ID, 'save-blackout')
    CANCEL_BUTTON = (By.ID, 'cancel-edit-of-blackout')

    @staticmethod
    def blackout_delete_loc(blackout_date):
        return By.XPATH, f'//tr[contains(., "{blackout_date.strftime("%Y-%m-%d")}")]//button'

    def navigate_to_datepicker_month(self, month):
        while month != self.element(BlackoutsPage.CALENDAR_MONTH).text:
            self.wait_for_element_and_click(BlackoutsPage.CALENDAR_FORWARD_BUTTON)
            time.sleep(util.get_click_sleep())

    def select_blackout_date(self, blackout_date_pair):
        start_date_str = blackout_date_pair[0].strftime('%Y-%m-%d')
        end_date_str = blackout_date_pair[1].strftime('%Y-%m-%d')
        self.navigate_to_datepicker_month(blackout_date_pair[0].strftime('%B %Y'))
        self.wait_for_element_and_click((By.XPATH, f'//div[contains(@class, "id-{start_date_str}")]'))
        self.navigate_to_datepicker_month(blackout_date_pair[1].strftime('%B %Y'))
        self.wait_for_element_and_click((By.XPATH, f'//div[contains(@class, "id-{end_date_str}")]'))

    def create_blackout_date(self, blackout_date_pair):
        today = datetime.date.today()
        if blackout_date_pair[1] < today:
            app.logger.info('Skipping blackout date since the end date is in the past')
        else:
            if blackout_date_pair[0] < today:
                blackout_date_pair[0] = today
            start_date_str = blackout_date_pair[0].strftime('%Y-%m-%d')
            end_date_str = blackout_date_pair[1].strftime('%Y-%m-%d')
            app.logger.info(f'Creating blackout called "{start_date_str}" starting "{start_date_str}" ending "{end_date_str}"')
            self.reload_page()
            self.wait_for_element_and_click(BlackoutsPage.CREATE_NEW_BUTTON)
            self.wait_for_element_and_type(BlackoutsPage.NAME_INPUT, start_date_str)
            self.select_blackout_date(blackout_date_pair)
            self.wait_for_element_and_click(BlackoutsPage.SAVE_BUTTON)

    def delete_blackout(self, blackout_date):
        app.logger.info(f'Deleting a blackout on "{blackout_date.strftime("%Y-%m-%d")}"')
        self.wait_for_element_and_click(BlackoutsPage.blackout_delete_loc(blackout_date))
        self.when_not_present(BlackoutsPage.blackout_delete_loc(blackout_date), util.get_short_timeout())

    def delete_all_blackouts(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.presence_of_element_located(BlackoutsPage.CREATE_NEW_BUTTON))
        for el in self.elements(BlackoutsPage.DELETE_BUTTON):
            app.logger.info('Deleting a blackout')
            el.click()
            time.sleep(1)

    def create_all_blackouts(self):
        for date_pair in util.get_blackout_date_ranges():
            self.create_blackout_date(date_pair)
            Wait(self.driver, util.get_short_timeout()).until(
                ec.presence_of_element_located(BlackoutsPage.blackout_delete_loc(date_pair[0])),
            )
