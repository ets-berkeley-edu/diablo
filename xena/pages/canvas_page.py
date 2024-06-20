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
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.page import Page
from xena.test_utils import util


class CanvasPage(Page):

    # CANVAS

    FRAME = (By.XPATH, '//iframe[starts-with(@id, "tool_content")]')
    DELETE_COURSE_BUTTON = (By.XPATH, '//button[text()="Delete Course"]')
    DELETE_COURSE_SUCCESS = (By.XPATH, '//*[contains(.,"successfully deleted")]')

    # RIPLEY

    # Create Site
    CREATE_SITE_LINK = (By.ID, 'create-course-site')
    CREATE_SITE_NEXT_BUTTON = (By.ID, 'go-next-btn')
    SWITCH_TO_CCN_BUTTON = (By.ID, 'radio-btn-mode-section-id')
    CCN_TEXT_AREA = (By.ID, 'page-create-course-site-section-id-list')
    REVIEW_CCNS_BUTTON = (By.ID, 'sections-by-ids-button')
    EXPAND_SECTIONS_BUTTON = (By.XPATH, '//button[contains(@id, "sections-course-")]')
    NEXT_BUTTON = (By.ID, 'page-create-course-site-continue')
    SITE_NAME_INPUT = (By.ID, 'course-site-name')
    SITE_ABBREV_INPUT = (By.ID, 'course-site-abbreviation')
    CREATE_SITE_BUTTON = (By.ID, 'create-course-site-button')

    # Add User
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
    def term_loc():
        current_term = app.config['CURRENT_TERM_NAME']
        return By.XPATH, f'//span[contains(., "{current_term}")]/..'

    @staticmethod
    def section_cbx_loc(section_id):
        return By.ID, f'template-canvas-manage-sections-checkbox-{section_id}'

    @staticmethod
    def user_cbx_loc(user):
        return By.XPATH, f'//td[contains(.,"{user.uid}")]/ancestor::tr//input[@name="selectedUser"]'

    def hide_canvas_footer(self):
        el_id = 'element_toggler_0'
        el_loc = By.ID, el_id
        if self.is_present(el_loc) and self.element(el_loc):
            self.driver.execute_script('document.getElementById("element_toggler_0").style.display="none";')

    def wait_for_ripley_frame_and_switch(self):
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.ripley_form_loc()))
        self.hide_canvas_footer()
        Wait(self.driver, util.get_medium_timeout()).until(ec.frame_to_be_available_and_switch_to_it(CanvasPage.FRAME))

    def provision_site(self, section, section_ids, site):
        epoch = int(time.time())
        site.name = f'{site.name} {epoch}'
        site.code = f'{site.code} {epoch}'
        app.logger.info(f'Creating a site named {site.code} for {section.code} sections {section_ids}')

        # Load tool
        admin_id = app.config['CANVAS_ADMIN_ID']
        tool_id = app.config['CANVAS_SITE_CREATION_TOOL']
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/users/{admin_id}/external_tools/{tool_id}')
        self.wait_for_ripley_frame_and_switch()
        self.when_present(CanvasPage.CREATE_SITE_LINK, util.get_medium_timeout())
        self.click_element_js(CanvasPage.CREATE_SITE_LINK)
        self.wait_for_element_and_click(CanvasPage.CREATE_SITE_NEXT_BUTTON)

        # Select sections by CCN
        self.when_present(CanvasPage.SWITCH_TO_CCN_BUTTON, util.get_short_timeout())
        self.click_element_js(CanvasPage.SWITCH_TO_CCN_BUTTON)
        self.wait_for_page_and_click(CanvasPage.term_loc())
        self.wait_for_element_and_type(CanvasPage.CCN_TEXT_AREA, ', '.join(section_ids))
        self.wait_for_page_and_click(CanvasPage.REVIEW_CCNS_BUTTON)
        if not self.is_present(self.section_cbx_loc(section_ids[0])):
            self.wait_for_element_and_click(CanvasPage.EXPAND_SECTIONS_BUTTON)
        for section_id in section_ids:
            self.when_present(CanvasPage.section_cbx_loc(section_id), 2)
            self.click_element_js(CanvasPage.section_cbx_loc(section_id))
        self.wait_for_page_and_click_js(CanvasPage.NEXT_BUTTON)

        # Name and create site; store site ID
        self.scroll_to_bottom()
        self.when_present(CanvasPage.SITE_NAME_INPUT, util.get_short_timeout())
        self.remove_and_enter_chars(CanvasPage.SITE_NAME_INPUT, f'{site.name}')
        self.remove_and_enter_chars(CanvasPage.SITE_ABBREV_INPUT, f'{site.code}')
        self.wait_for_page_and_click(CanvasPage.CREATE_SITE_BUTTON)
        Wait(self.driver, util.get_long_timeout()).until(ec.url_contains('/courses/'))
        parts = self.driver.current_url.split('/')
        site.site_id = [i for i in parts if i][-1]
        app.logger.info(f'Site {site.code} ID is {site.site_id}')
        section.sites.append(site)

    def delete_site(self, site_id):
        app.logger.info(f'Deleting course site ID {site_id}')
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site_id}/confirm_action?event=delete')
        self.wait_for_page_and_click_js(CanvasPage.DELETE_COURSE_BUTTON)
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(CanvasPage.DELETE_COURSE_SUCCESS))

    def add_teacher_to_site(self, site, section, user):
        app.logger.info(f'Adding UID {user.uid} to site ID {site.site_id} section {section.number} as a Teacher')
        self.driver.get(f"{app.config['CANVAS_BASE_URL']}/courses/{site.site_id}/external_tools/{app.config['CANVAS_ADD_USER_TOOL']}")
        self.wait_for_ripley_frame_and_switch()
        self.wait_for_page_and_click_js(self.SEARCH_BY_UID, util.get_short_timeout())
        self.remove_and_enter_chars(self.SEARCH_TERM_INPUT, user.uid)
        self.wait_for_element_and_click(self.SEARCH_BUTTON)
        self.wait_for_element_and_click(self.user_cbx_loc(user))
        opt = self.element((By.XPATH, f'//option[contains(text(), "{section.code} {section.number}")]'))
        opt.click()
        role_select = Select(self.element(self.ROLE_SELECT))
        role_select.select_by_visible_text('Teacher')
        self.wait_for_element_and_click(self.ADD_USER_BUTTON)
        self.when_present(self.SUCCESS_MSG, util.get_medium_timeout())

    # KALTURA

    @staticmethod
    def kaltura_form_loc():
        tool_url = app.config['KALTURA_TOOL_URL']
        return By.XPATH, f'//form[contains(@action, "{tool_url}")]'

    def is_tool_configured(self, tool_id):
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/api/v1/accounts/{app.config["CANVAS_ROOT_ACCOUNT"]}/external_tools/{tool_id}')
        loc = By.XPATH, '//pre'
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(loc))
        json_string = self.element(loc).text
        return True if f'{app.config["KALTURA_TOOL_URL"]}' in json_string else False
