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
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.page import Page
from xena.test_utils import util


class CanvasPage(Page):

    # CANVAS

    FRAME = (By.XPATH, '//iframe[starts-with(@id, "tool_content")]')
    DELETE_COURSE_BUTTON = (By.XPATH, '//button[text()="Delete Course"]')
    DELETE_COURSE_SUCCESS = (By.XPATH, '//*[contains(.,"successfully deleted")]')

    def hide_canvas_footer(self):
        el_id = 'element_toggler_0'
        el_loc = By.ID, el_id
        if self.is_present(el_loc) and self.element(el_loc):
            self.driver.execute_script('document.getElementById("element_toggler_0").style.display="none";')

    # CREATE GENERIC COURSE SITE

    ADD_NEW_COURSE_BUTTON = By.XPATH, '//button[@aria-label="Create new course"]'
    COURSE_NAME_INPUT = By.XPATH, '(//form[@aria-label="Add a New Course"]//input)[1]'
    REF_CODE_INPUT = By.XPATH, '(//form[@aria-label="Add a New Course"]//input)[2]'
    TERM_SELECT = By.ID, 'course_enrollment_term_id'
    CREATE_COURSE_BUTTON = By.XPATH, '//button[contains(.,"Add Course")]'
    SEARCH_COURSE_INPUT = By.XPATH, '//input[@placeholder="Search courses..."]'
    PUBLISH_STATUS = By.XPATH, '//button[@data-position-target="course_publish_menu"]'
    ADD_COURSE_SUCCESS = By.XPATH, '//p[contains(.,"successfully added!")]'

    def create_site(self, section, site):
        epoch = int(time.time())
        site.name = f'{site.name} {epoch}'
        site.code = f'{site.code} {epoch}'
        app.logger.info(f'Creating a site named {site.code}')
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/accounts/{app.config["CANVAS_QA_ACCOUNT"]}')
        self.wait_for_page_and_click(self.ADD_NEW_COURSE_BUTTON)
        self.wait_for_element_and_type(self.COURSE_NAME_INPUT, site.name)
        self.wait_for_element_and_type(self.REF_CODE_INPUT, site.code)
        self.wait_for_element_and_click(self.CREATE_COURSE_BUTTON)
        self.when_present(self.ADD_COURSE_SUCCESS, util.get_medium_timeout())
        self.search_for_site(site)
        app.logger.info(f'Site {site.code} ID is {site.site_id}')
        section.sites.append(site)

    @staticmethod
    def course_site_link_loc(site):
        return By.XPATH, f'//a[contains(., "{site.name}")]'

    def search_for_site(self, site):
        tries = 0
        while tries <= 6:
            tries += 1
            try:
                app.logger.info(f'Search for {site.name}')
                self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/accounts/{app.config["CANVAS_QA_ACCOUNT"]}')
                self.wait_for_element_and_type(self.SEARCH_COURSE_INPUT, site.name)
                time.sleep(1)
                self.wait_for_element_and_click(self.course_site_link_loc(site))
                self.when_present(self.PUBLISH_STATUS, util.get_short_timeout())
                site.site_id = self.driver.current_url.replace(f'{app.config["CANVAS_BASE_URL"]}/courses/', '')
                break
            except (NoSuchElementException, TimeoutError):
                if tries == 6:
                    raise
                else:
                    time.sleep(1)

    def delete_site(self, site_id):
        app.logger.info(f'Deleting course site ID {site_id}')
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site_id}/confirm_action?event=delete')
        self.wait_for_page_and_click_js(CanvasPage.DELETE_COURSE_BUTTON)
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(CanvasPage.DELETE_COURSE_SUCCESS))

    # RIPLEY ADD USER

    SEARCH_TERM_INPUT = By.ID, 'search-text'
    SEARCH_BY_UID = By.ID, 'radio-btn-uid'
    SEARCH_BUTTON = By.ID, 'add-user-submit-search-btn'
    SECTION_SELECT = By.ID, 'course-section'
    ROLE_SELECT = By.ID, 'user-role'
    ADD_USER_BUTTON = By.ID, 'add-user-btn'
    SUCCESS_MSG = By.ID, 'success-message'

    @staticmethod
    def ripley_form_loc():
        ripley_url = app.config['RIPLEY_BASE_URL']
        return By.XPATH, f'//form[contains(@action, "{ripley_url}")]'

    @staticmethod
    def user_cbx_loc(user):
        return By.XPATH, f'//td[contains(.,"{user.uid}")]/ancestor::tr//input[@name="selectedUser"]'

    def wait_for_ripley_frame_and_switch(self):
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.ripley_form_loc()))
        self.hide_canvas_footer()
        Wait(self.driver, util.get_medium_timeout()).until(ec.frame_to_be_available_and_switch_to_it(CanvasPage.FRAME))

    def add_teacher_to_site(self, site, user, section=None):
        app.logger.info(f'Adding UID {user.uid} to site ID {site.site_id} as a Teacher')
        self.driver.get(f"{app.config['CANVAS_BASE_URL']}/courses/{site.site_id}/external_tools/{app.config['CANVAS_ADD_USER_TOOL']}")
        self.wait_for_ripley_frame_and_switch()
        self.wait_for_page_and_click_js(self.SEARCH_BY_UID)
        self.remove_and_enter_chars(self.SEARCH_TERM_INPUT, user.uid)
        self.wait_for_page_and_click_js(self.SEARCH_BUTTON)
        self.wait_for_element_and_click(self.user_cbx_loc(user))
        if section:
            opt = self.element((By.XPATH, f'//option[contains(text(), "{section.code} {section.number}")]'))
            opt.click()
        role_select = Select(self.element(self.ROLE_SELECT))
        role_select.select_by_visible_text('Teacher')
        self.wait_for_element_and_click(self.ADD_USER_BUTTON)
        self.when_present(self.SUCCESS_MSG, util.get_medium_timeout())
