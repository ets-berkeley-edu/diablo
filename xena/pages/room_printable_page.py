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

import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class RoomPrintablePage(DiabloPages):

    PRINT_SCHED_LINK = (By.XPATH, '//a[contains(text(), "Print schedule")]')
    ROOM_NAME = (By.XPATH, '//h2')

    def open_printable_schedule(self):
        app.logger.info('Opening the printable room schedule')
        self.wait_for_page_and_click_js(RoomPrintablePage.PRINT_SCHED_LINK)
        time.sleep(1)
        windows = self.window_handles()
        self.switch_to_last_window(windows)
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(RoomPrintablePage.ROOM_NAME))

    def close_printable_schedule(self):
        app.logger.info('Closing the printable room schedule')
        if len(self.window_handles()) > 1:
            self.close_window_and_switch()

    def visible_course(self, section):
        return self.element((By.ID, f'course-{section.ccn}-label')).text.strip()

    def visible_instructors(self, section):
        els = self.elements((By.XPATH, f'//div[contains(@id, "course-{section.ccn}-instructor-")]'))
        return [el.text.strip() for el in els]

    def visible_days(self, section):
        els = self.elements((By.XPATH, f'//td[@id="course-{section.ccn}-days"]/div'))
        return [el.text.strip() for el in els]

    def visible_times(self, section):
        els = self.elements((By.XPATH, f'//td[@id="course-{section.ccn}-times"]/div'))
        return [el.get_attribute('innerText').strip() for el in els]

    def visible_recording_type(self, section):
        return self.element((By.ID, f'course-{section.ccn}-recording-type')).text.strip()

    # ACTUAL VS EXPECTED

    def verify_printable(self, section, meeting, recording_schedule):
        self.open_printable_schedule()

        expected_course = f'{section.code}, {section.number}'
        assert self.visible_course(section) == expected_course

        expected_instr = [f'{inst.first_name} {inst.last_name} ({inst.uid})'.strip() for inst in section.instructors]
        assert self.visible_instructors(section) == expected_instr

        expected_days = [f'{meeting.days}']
        assert self.visible_days(section) == expected_days

        dates = f'{meeting.start_date.strftime("%b %-d, %Y")} - {meeting.end_date.strftime("%b %-d, %Y")}'
        times = f'{meeting.start_time} - {meeting.end_time}'
        assert self.visible_times(section) == [f'{dates}\n{times}']

        expected_type = recording_schedule.recording_type.value['printable']
        assert self.visible_recording_type(section) == expected_type

        self.close_printable_schedule()
