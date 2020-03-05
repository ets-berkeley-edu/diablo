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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.test_utils import util


class Page(object):

    def __init__(self, driver):
        self.driver = driver

    def element(self, locator):
        strategy = locator[0]
        target = locator[1]
        if strategy == 'id':
            return self.driver.find_element_by_id(target)
        elif strategy == 'name':
            return self.driver.find_element_by_name(target)

    def wait_for_element(self, locator):
        Wait(self.driver, util.get_short_timeout()).until(ec.presence_of_element_located(locator))
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(locator))

    def click_element(self, locator):
        self.wait_for_element(locator)
        self.element(locator).click()

    def wait_for_element_and_click(self, locator):
        self.wait_for_element(locator)
        self.click_element(locator)

    def wait_for_element_and_type(self, locator, string):
        self.wait_for_element_and_click(locator)
        self.element(locator).clear()
        self.element(locator).send_keys(string)

    def wait_for_title(self, string):
        app.logger.info(f'Waiting for page title \'{string}\'')
        Wait(self.driver, util.get_long_timeout()).until((ec.title_is(string)))

    def hit_enter(self):
        ActionChains(self.driver).send_keys(Keys.ENTER).perform()
