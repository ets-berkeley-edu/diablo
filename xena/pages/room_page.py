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

from flask import current_app as app
from selenium.webdriver.common.by import By
from xena.models.capability import Capability
from xena.pages.diablo_pages import DiabloPages


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
