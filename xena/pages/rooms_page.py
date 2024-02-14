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

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class RoomsPage(DiabloPages):

    SEARCH_INPUT = (By.XPATH, '//input')
    ROOM_LINK = (By.XPATH, '//a[contains(@id, "room-")]')

    @staticmethod
    def room_row_locator(room):
        return By.XPATH, f'//a[text()="{room.name}"]'

    def hit_url(self):
        self.driver.get(f'{app.config["BASE_URL"]}/rooms')

    def load_page(self):
        app.logger.info('Loading Rooms page')
        self.hit_url()

    def search_rooms(self, string):
        app.logger.info(f'Searching for room {string}')
        self.wait_for_element_and_type(RoomsPage.SEARCH_INPUT, string)

    def wait_for_room_result(self, room):
        self.wait_for_element(RoomsPage.room_row_locator(room), util.get_short_timeout())

    def find_room(self, room):
        self.search_rooms(room.name)
        self.wait_for_room_result(room)

    def wait_for_rooms_list(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_any_elements_located(RoomsPage.ROOM_LINK))

    def click_room_link(self, room):
        self.wait_for_element_and_click(RoomsPage.room_row_locator(room))
