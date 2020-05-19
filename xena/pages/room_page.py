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
from datetime import datetime

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.models.capability import Capability
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class RoomPage(DiabloPages):

    SELECT_CAPABILITY_INPUT = (By.XPATH, '//input[contains(@id, "select-room-capability")]/ancestor::div[@role="button"]')
    AUDITORIUM_TOGGLE = (By.XPATH, '//label[text()="Auditorium"]/preceding-sibling::div')

    def auditorium_selected(self):
        el = self.element((By.XPATH, '//label[text()="Auditorium"]/preceding-sibling::div/input'))
        return el.get_attribute('aria-checked') == 'true'

    def click_auditorium_toggle(self):
        app.logger.info('Clicking the auditorium toggle')
        self.wait_for_element_and_click(RoomPage.AUDITORIUM_TOGGLE)

    def set_capability(self, capability):
        app.logger.info(f'Setting room capability "{capability.value}"')
        if (capability == Capability.SCREENCAST_AND_VIDEO) and not self.auditorium_selected():
            self.click_auditorium_toggle()
        self.wait_for_element_and_click(RoomPage.SELECT_CAPABILITY_INPUT)
        self.click_menu_option(capability.value)
        time.sleep(1)

    @staticmethod
    def series_row_xpath(recording_sched):
        return f'//div[@id="kaltura-event-list"]//tr[contains(., "{recording_sched.series_id}")]'

    def wait_for_series_row(self, recording_sched):
        xpath = RoomPage.series_row_xpath(recording_sched)
        Wait(self.driver, util.get_short_timeout()).until(ec.presence_of_element_located((By.XPATH, xpath)))

    def series_row_kaltura_link_text(self, recording_sched):
        return self.element((By.XPATH, f'{RoomPage.series_row_xpath(recording_sched)}//a')).text.strip()

    def series_row_start_date(self, recording_sched):
        text = self.element((By.XPATH, f'{RoomPage.series_row_xpath(recording_sched)}/td[4]/span')).text.strip()
        return datetime.strptime(text, '%a, %b %d, %Y')

    def series_row_end_date(self, recording_sched):
        text = self.element((By.XPATH, f'{RoomPage.series_row_xpath(recording_sched)}/td[5]/span')).text.strip()
        return datetime.strptime(text, '%a, %b %d, %Y')

    def series_row_duration(self, recording_sched):
        return self.element((By.XPATH, f'{RoomPage.series_row_xpath(recording_sched)}/td[6]/span')).text.strip()

    def series_row_days(self, recording_sched):
        return self.element((By.XPATH, f'{RoomPage.series_row_xpath(recording_sched)}/td[7]')).text.strip()

    def expand_series_row(self, recording_sched):
        app.logger.info(f'Expanding series recordings for Kaltura series ID {recording_sched.series_id}')
        self.scroll_to_bottom()
        self.wait_for_element_and_click((By.XPATH, f'{RoomPage.series_row_xpath(recording_sched)}//button'))

    @staticmethod
    def series_recording_xpath(recording_sched):
        return f'{RoomPage.series_row_xpath(recording_sched)}/following-sibling::tr//tbody/tr'

    def series_recording_rows(self, recording_sched):
        return self.elements((By.XPATH, f'{RoomPage.series_recording_xpath(recording_sched)}'))

    def series_recording_cell_values(self, recording_sched, cell_node):
        values = []
        current_year = app.config['CURRENT_TERM_BEGIN'].split('-')[0]
        els = self.series_recording_rows(recording_sched)
        for el in els:
            index = els.index(el)
            cell = self.element((By.XPATH, f'{RoomPage.series_recording_xpath(recording_sched)}[{index + 1}]/td[{cell_node}]'))
            recording_time = datetime.strptime(f'{cell.text}, {current_year}', '%I:%M%p, %a, %b %d, %Y')
            values.append(recording_time)
        return values

    def series_recording_start_times(self, recording_sched):
        return self.series_recording_cell_values(recording_sched, '3')

    def series_recording_end_times(self, recording_sched):
        return self.series_recording_cell_values(recording_sched, '4')
