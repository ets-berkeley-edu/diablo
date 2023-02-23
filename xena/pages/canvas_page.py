"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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
from xena.models.kaltura_lti_tool import KalturaLTITool
from xena.pages.calnet_page import CalNetPage
from xena.pages.page import Page
from xena.test_utils import util


class CanvasPage(Page):

    # CANVAS

    ADMIN_LINK = (By.ID, 'global_nav_accounts_link')

    FRAME = (By.ID, 'tool_content')
    MASQUERADE_LINK = (By.XPATH, '//a[contains(@href, "masquerade")]')
    STOP_MASQUERADE_LINK = (By.CLASS_NAME, 'stop_masquerading')
    ACCEPT_INVITE_BUTTON = (By.NAME, 'accept')

    DELETE_COURSE_BUTTON = (By.XPATH, '//button[text()="Delete Course"]')
    DELETE_COURSE_SUCCESS = (By.XPATH, '//*[contains(.,"successfully deleted")]')

    NAVIGATION_LINK = (By.LINK_TEXT, 'Navigation')
    TOOL_SAVE_BUTTON = (By.XPATH, '//button[text()="Save"]')
    MEDIA_GALLERY_LINK = (By.LINK_TEXT, 'Media Gallery')
    MY_MEDIA_LINK = (By.LINK_TEXT, 'My Media')

    # JUNCTION

    CREATE_SITE_LINK = (By.LINK_TEXT, 'Create a Course Site')
    SWITCH_TO_CCN_BUTTON = (By.XPATH, '//button[contains(.,"Switch to CCN input")]')
    CCN_TEXT_AREA = (By.ID, 'bc-page-create-course-site-ccn-list')
    REVIEW_CCNS_BUTTON = (By.XPATH, '//button[contains(text(), "Review matching CCNs")]')
    NEXT_BUTTON = (By.XPATH, '//button[contains(text(), "Next")]')
    SITE_NAME_INPUT = (By.ID, 'siteName')
    SITE_ABBREV_INPUT = (By.ID, 'siteAbbreviation')
    CREATE_SITE_BUTTON = (By.XPATH, '//button[contains(text(), "Create Course Site")]')

    @staticmethod
    def junction_form_loc():
        junction_url = app.config['JUNCTION_BASE_URL']
        return By.XPATH, f'//form[contains(@action, "{junction_url}")]'

    @staticmethod
    def term_loc():
        current_term = app.config['CURRENT_TERM_NAME']
        return By.XPATH, f'//label[contains(., "{current_term}")]/..'

    def hit_homepage(self):
        self.driver.get(app.config['CANVAS_BASE_URL'])

    def hide_canvas_footer(self):
        el_id = 'element_toggler_0'
        el_loc = By.ID, el_id
        if self.is_present(el_loc) and self.element(el_loc):
            self.driver.execute_script('document.getElementById("element_toggler_0").style.display="none";')

    def log_in(self):
        app.logger.info('Logging in to Canvas')
        self.hit_homepage()
        self.wait_for_element_and_type(CalNetPage.USERNAME_INPUT, 'PLEASE LOG IN MANUALLY')
        Wait(self.driver, util.get_long_timeout()).until(ec.presence_of_element_located(CanvasPage.ADMIN_LINK))

    def masquerade_as(self, user, site_id=None):
        app.logger.info(f'Masquerading as Canvas ID {user.canvas_id}')
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/users/{user.canvas_id}/masquerade')
        self.wait_for_element_and_click(CanvasPage.MASQUERADE_LINK)
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(CanvasPage.STOP_MASQUERADE_LINK))
        if site_id:
            self.load_site(site_id)

    def stop_masquerading(self):
        app.logger.info('Ending masquerade')
        self.hit_homepage()
        self.wait_for_page_and_click(CanvasPage.STOP_MASQUERADE_LINK)
        Wait(self.driver, util.get_medium_timeout()).until(ec.staleness_of)

    def load_site(self, site_id):
        app.logger.info(f'Loading course site ID "{site_id}"')
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site_id}')
        Wait(self.driver, util.get_medium_timeout()).until(ec.url_contains(site_id))
        if self.is_present(CanvasPage.ACCEPT_INVITE_BUTTON):
            self.wait_for_element_and_click(CanvasPage.ACCEPT_INVITE_BUTTON)
            self.when_not_present(CanvasPage.ACCEPT_INVITE_BUTTON)

    def provision_site(self, section, section_ids, site):
        epoch = int(time.time())
        site.name = f'{site.name} {epoch}'
        site.code = f'{site.code} {epoch}'
        app.logger.info(f'Creating a site named {site.code} for {section.code} sections {section_ids}')

        # Load tool
        admin_id = app.config['CANVAS_ADMIN_ID']
        tool_id = app.config['CANVAS_SITE_CREATION_TOOL']
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/users/{admin_id}/external_tools/{tool_id}')
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.junction_form_loc()))
        self.hide_canvas_footer()
        Wait(self.driver, util.get_medium_timeout()).until(ec.frame_to_be_available_and_switch_to_it(CanvasPage.FRAME))
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(CanvasPage.CREATE_SITE_LINK))
        self.wait_for_element_and_click(CanvasPage.CREATE_SITE_LINK)

        # Select sections by CCN
        self.wait_for_element(CanvasPage.SWITCH_TO_CCN_BUTTON, util.get_long_timeout())
        self.wait_for_page_and_click(CanvasPage.SWITCH_TO_CCN_BUTTON)
        self.wait_for_page_and_click(CanvasPage.term_loc())
        self.wait_for_element_and_type(CanvasPage.CCN_TEXT_AREA, ', '.join(section_ids))
        self.wait_for_page_and_click(CanvasPage.REVIEW_CCNS_BUTTON)
        self.wait_for_page_and_click_js(CanvasPage.NEXT_BUTTON)

        # Name and create site; store site ID
        self.scroll_to_bottom()
        self.wait_for_element_and_type(CanvasPage.SITE_NAME_INPUT, f'{site.name}')
        self.wait_for_element_and_type(CanvasPage.SITE_ABBREV_INPUT, f'{site.code}')
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

    def delete_section_sites(self, section):
        site_ids = util.get_course_site_ids(section)
        for site_id in site_ids:
            self.delete_site(site_id)
        return site_ids

    # KALTURA

    @staticmethod
    def kaltura_form_loc():
        tool_url = app.config['KALTURA_TOOL_URL']
        return By.XPATH, f'//form[contains(@action, "{tool_url}")]'

    @staticmethod
    def tool_nav_link_locator(tool):
        return By.XPATH, f'//ul[@id="section-tabs"]//a[text()="{tool.value}"]'

    @staticmethod
    def disabled_tool_locator(tool):
        return By.XPATH, f'//ul[@id="nav_disabled_list"]/li[contains(.,"{tool.value}")]//a'

    @staticmethod
    def enable_tool_link_locator(tool):
        return By.XPATH, f'//ul[@id="nav_disabled_list"]/li[contains(.,"{tool.value}")]//a[@title="Enable this item"]'

    @staticmethod
    def enabled_tool_locator(tool):
        return By.XPATH, f'//ul[@id="nav_enabled_list"]/li[contains(.,"{tool.value}")]'

    def enable_tool(self, site, tool):
        if self.is_present(CanvasPage.tool_nav_link_locator(tool)):
            app.logger.info(f'{tool} is already enabled')
        else:
            app.logger.info(f'Enabling {tool} on site ID {site.site_id}')
            self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site.site_id}/settings')
            self.wait_for_page_and_click(CanvasPage.NAVIGATION_LINK)
            self.hide_canvas_footer()
            self.wait_for_element_and_click(CanvasPage.disabled_tool_locator(tool))
            self.wait_for_element_and_click(CanvasPage.enable_tool_link_locator(tool))
            Wait(self.driver, util.get_medium_timeout()).until(
                ec.visibility_of_element_located(CanvasPage.enabled_tool_locator(tool)),
            )
            self.wait_for_element_and_click(CanvasPage.TOOL_SAVE_BUTTON)
            Wait(self.driver, util.get_medium_timeout()).until(
                ec.visibility_of_element_located(CanvasPage.tool_nav_link_locator(tool)),
            )

    def enable_media_gallery(self, site):
        self.enable_tool(site, KalturaLTITool.MEDIA_GALLERY)

    def enable_my_media(self, site):
        self.enable_tool(site, KalturaLTITool.MY_MEDIA)

    def click_media_gallery_tool(self):
        app.logger.info('Clicking the Media Gallery LTI tool')
        self.hide_canvas_footer()
        self.wait_for_page_and_click(CanvasPage.MEDIA_GALLERY_LINK)
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.kaltura_form_loc()))

    def click_my_media_tool(self):
        app.logger.info('Clicking the My Media LTI tool')
        self.hide_canvas_footer()
        self.wait_for_page_and_click(CanvasPage.MY_MEDIA_LINK)
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.kaltura_form_loc()))

    def load_media_gallery_tool(self, site):
        app.logger.info(f'Loading Media Gallery on site ID {site.site_id}')
        tool_id = app.config['CANVAS_MEDIA_GALLERY_TOOL']
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site.site_id}/external_tools/{tool_id}')
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.kaltura_form_loc()))

    def load_my_media_tool(self, site):
        app.logger.info(f'Loading My Media on site ID {site.site_id}')
        tool_id = app.config['CANVAS_MY_MEDIA_TOOL']
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site.site_id}/external_tools/{tool_id}')
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.kaltura_form_loc()))

    def is_tool_configured(self, tool_id):
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/api/v1/accounts/{app.config["CANVAS_ROOT_ACCOUNT"]}/external_tools/{tool_id}')
        loc = By.XPATH, '//pre'
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(loc))
        json_string = self.element(loc).text
        return True if f'{app.config["KALTURA_TOOL_URL"]}' in json_string else False
