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
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
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
    DELETE_COURSE_SUCCESS = (By.XPATH, '//li[contains(.,"successfully deleted")]')

    MEDIA_GALLERY_LINK = (By.LINK_TEXT, 'Media Gallery')
    MY_MEDIA_LINK = (By.LINK_TEXT, 'My Media')

    # JUNCTION

    CREATE_SITE_LINK = (By.LINK_TEXT, 'Create a Course Site')
    SWITCH_TO_CCN_BUTTON = (By.XPATH, '//button[@data-ng-click="toggleAdminMode()"]')
    CCN_TEXT_AREA = (By.ID, 'bc-page-create-course-site-ccn-list')
    REVIEW_CCNS_BUTTON = (By.XPATH, '//button[text()="Review matching CCNs"]')
    NEXT_BUTTON = (By.XPATH, '//button[text()="Next"]')
    SITE_NAME_INPUT = (By.ID, 'siteName')
    SITE_ABBREV_INPUT = (By.ID, 'siteAbbreviation')
    CREATE_SITE_BUTTON = (By.XPATH, '//button[text()="Create Course Site"]')

    @staticmethod
    def form_loc():
        junction_url = app.config['JUNCTION_BASE_URL']
        return By.XPATH, f'//form[contains(@action, "{junction_url}")]'

    @staticmethod
    def term_loc():
        current_term = app.config['CURRENT_TERM_NAME']
        return By.XPATH, f'//label[text()="{current_term}"]/preceding-sibling::input'

    def hit_homepage(self):
        self.driver.get(app.config['CANVAS_BASE_URL'])

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
        app.logger.info(f'Creating a site for {section.code} sections {section_ids}')

        # Load tool
        admin_id = app.config['CANVAS_ADMIN_ID']
        tool_id = app.config['CANVAS_SITE_CREATION_TOOL']
        self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/users/{admin_id}/external_tools/{tool_id}')
        Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(CanvasPage.form_loc()))
        Wait(self.driver, util.get_medium_timeout()).until(ec.frame_to_be_available_and_switch_to_it(CanvasPage.FRAME))
        self.wait_for_element_and_click(CanvasPage.CREATE_SITE_LINK)

        # Select sections by CCN
        self.wait_for_element(CanvasPage.SWITCH_TO_CCN_BUTTON, util.get_long_timeout())
        self.wait_for_page_and_click_js(CanvasPage.SWITCH_TO_CCN_BUTTON)
        self.wait_for_page_and_click_js(CanvasPage.term_loc())
        self.wait_for_element_and_type(CanvasPage.CCN_TEXT_AREA, ', '.join(section_ids))
        self.wait_for_page_and_click(CanvasPage.REVIEW_CCNS_BUTTON)
        self.wait_for_page_and_click(CanvasPage.NEXT_BUTTON)

        # Name and create site; store site ID
        self.wait_for_element_and_type(CanvasPage.SITE_NAME_INPUT, f'{site.name}')
        self.wait_for_element_and_type(CanvasPage.SITE_ABBREV_INPUT, f'{site.code}')
        self.wait_for_element_and_click(CanvasPage.CREATE_SITE_BUTTON)
        Wait(self.driver, util.get_long_timeout()).until(ec.url_contains('/courses/'))
        parts = self.driver.current_url.split('/')
        site.site_id = [i for i in parts if i][-1]
        section.sites.append(site)

    def delete_sites(self, section):
        site_ids = util.get_course_site_ids(section)
        for site_id in site_ids:
            app.logger.info(f'Deleting course site ID #{site_id}')
            self.driver.get(f'{app.config["CANVAS_BASE_URL"]}/courses/{site_id}/confirm_action?event=delete')
            self.wait_for_page_and_click_js(CanvasPage.DELETE_COURSE_BUTTON)
            Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(CanvasPage.DELETE_COURSE_SUCCESS))
            util.delete_course_site(site_id)

    def click_media_gallery_tool(self):
        app.logger.info('Clicking the Media Gallery LTI tool')
        self.wait_for_page_and_click_js(CanvasPage.MEDIA_GALLERY_LINK)
        Wait(self.driver, util.get_medium_timeout()).until(ec.frame_to_be_available_and_switch_to_it(CanvasPage.FRAME))

    def click_my_media_tool(self):
        app.logger.info('Clicking the My Media LTI tool')
        self.wait_for_page_and_click_js(CanvasPage.MY_MEDIA_LINK)
        Wait(self.driver, util.get_medium_timeout()).until(ec.frame_to_be_available_and_switch_to_it(CanvasPage.FRAME))
