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
from xena.pages.diablo_pages import DiabloPages


class SignUpPage(DiabloPages):

    SECTION_ID = (By.XPATH, '//div[contains(text(), "Section ID:")]')
    COURSE_TITLE = (By.ID, 'course-title')
    INSTRUCTORS = (By.ID, 'instructors')
    INSTRUCTOR = (By.XPATH, '//*[contains(@id, "instructor-")]')
    MEETING_DAYS = (By.ID, 'meeting-days')
    MEETING_TIMES = (By.ID, 'meeting-times')
    ROOMS = (By.ID, 'rooms')
    CROSS_LISTING = (By.XPATH, '//span[contains(@id, "cross-listing")]')
    CC_EXPLAINED_LINK = (By.ID, 'link-to-course-capture-overview')
    RECORDING_TYPE_TOOLTIP_BUTTON = (By.XPATH, '//span[@id="tooltip-recording-type"]/following-sibling::i')
    PUBLISH_TOOLTIP_BUTTON = (By.XPATH, '//span[@id="tooltip-publish"]/following-sibling::i')
    VISIBLE_TOOLTIP = (By.XPATH, '//div[@class="v-tooltip__content menuable__content__active"]')
    RECORDING_TYPE_STATIC = (By.XPATH, '//input[@name="recordingType"]/..')
    SELECT_RECORDING_TYPE_INPUT = (By.XPATH, '//label[@id="select-recording-type-label"]')
    SELECT_PUBLISH_TYPE_INPUT = (By.XPATH, '//input[@id="select-publish-type"]/..')
    AGREE_TO_TERMS_CBX = (By.XPATH, '//input[@id="agree-to-terms-checkbox"]/..')
    CC_POLICIES_LINK = (By.ID, 'link-to-course-capture-policies')
    APPROVE_BUTTON = (By.ID, 'btn-approve')
    CONFIRMATION_MSG = (By.XPATH, '//span[contains(text(), "You submitted the preferences below.")]')

    RECORDING_TYPE_APPROVED = (By.XPATH, '//h4[contains(., "Recording Type")]/../following-sibling::div/div')
    PUBLISH_TYPE_APPROVED = (By.ID, 'approved-publish-type')

    RECORDING_TYPE_SCHEDULED = (By.XPATH, '//div[text()="Recording Type"]/following-sibling::div')
    PUBLISH_TYPE_SCHEDULED = (By.XPATH, '//div[text()="Publish Type"]/following-sibling::div')

    @staticmethod
    def instructor_link_locator(instructor):
        return By.ID, f'instructor-{instructor.uid}'

    @staticmethod
    def room_link_locator(room):
        return By.LINK_TEXT, room.name

    def load_page(self, section):
        app.logger.info(f'Loading sign-up page for term {section.term} section ID {section.ccn}')
        self.driver.get(f'{app.config["BASE_URL"]}/course/{section.term}/{section.ccn}')
        self.wait_for_diablo_title(f'{section.code}, {section.number}')

    # SIS DATA

    def visible_ccn(self):
        return self.element(SignUpPage.SECTION_ID).text.strip().split(' ')[2]

    def visible_course_title(self):
        return self.element(SignUpPage.COURSE_TITLE).text

    def visible_instructors(self):
        els = self.elements(SignUpPage.INSTRUCTOR)
        return [el.text for el in els]

    def visible_meeting_days(self):
        return self.element(SignUpPage.MEETING_DAYS).get_attribute('innerText').strip()

    def visible_meeting_time(self):
        return self.element(SignUpPage.MEETING_TIMES).get_attribute('innerText').strip()

    def visible_rooms(self):
        return self.element(SignUpPage.ROOMS).get_attribute('innerText').strip()

    def visible_cross_listing_codes(self):
        return [el.text for el in self.elements(SignUpPage.CROSS_LISTING)]

    def visible_cross_listing_ccns(self):
        return [el.get_attribute('id').split('-')[2] for el in self.elements(SignUpPage.CROSS_LISTING)]

    # CAPTURE + APPROVAL SETTINGS

    def instructor_approval_present(self, instructor):
        locator = (By.XPATH, f'//div[contains(text(), "{instructor.first_name} {instructor.last_name}")][contains(., "approved.")]')
        return self.is_present(locator)

    def admin_approval_present(self):
        locator = (By.XPATH, '//span[text()="(Course Capture administrator)"]/..[contains(., "approved.")]')
        return self.is_present(locator)

    def open_rec_type_tooltip(self):
        app.logger.info('Hovering over recording type tooltip')
        self.mouseover(self.element(SignUpPage.RECORDING_TYPE_TOOLTIP_BUTTON))
        self.wait_for_element(SignUpPage.VISIBLE_TOOLTIP, app.config['TIMEOUT_SHORT'])

    def open_publish_tooltip(self):
        app.logger.info('Hovering over publish tooltip')
        self.mouseover(self.element(SignUpPage.PUBLISH_TOOLTIP_BUTTON))
        self.wait_for_element(SignUpPage.VISIBLE_TOOLTIP, app.config['TIMEOUT_SHORT'])

    def visible_tooltip(self):
        return self.element(SignUpPage.VISIBLE_TOOLTIP).get_attribute('innerText').strip()

    def click_rec_type_input(self):
        app.logger.info('Clicking the recording type input')
        self.wait_for_element_and_click(SignUpPage.SELECT_RECORDING_TYPE_INPUT)

    def click_publish_type_input(self):
        app.logger.info('Clicking the publish type input')
        self.wait_for_element_and_click(SignUpPage.SELECT_PUBLISH_TYPE_INPUT)

    def select_rec_type(self, recording_type):
        app.logger.info(f'Selecting recording type {recording_type}')
        self.click_rec_type_input()
        self.click_menu_option(recording_type)

    def select_publish_type(self, publish_type):
        app.logger.info(f'Selecting publish type {publish_type}')
        self.click_publish_type_input()
        self.click_menu_option(publish_type)

    def click_agree_checkbox(self):
        app.logger.info('Clicking the agree-to-terms checkbox')
        self.wait_for_element_and_click(SignUpPage.AGREE_TO_TERMS_CBX)

    def click_approve_button(self):
        app.logger.info('Clicking the approve button')
        self.wait_for_element_and_click(SignUpPage.APPROVE_BUTTON)

    def wait_for_approval_confirmation(self):
        Wait(self.driver, app.config['TIMEOUT_SHORT']).until(
            method=ec.visibility_of_element_located(SignUpPage.CONFIRMATION_MSG),
            message=f'Failed wait_for_approval_confirmation: {SignUpPage.CONFIRMATION_MSG}',
        )

    def default_rec_type(self):
        return self.element(SignUpPage.RECORDING_TYPE_STATIC).text.strip()

    def approved_rec_type(self):
        return self.element(SignUpPage.RECORDING_TYPE_APPROVED).text.strip()

    def approved_publish_type(self):
        return self.element(SignUpPage.PUBLISH_TYPE_APPROVED).text.strip()

    def scheduled_rec_type(self):
        return self.element(SignUpPage.RECORDING_TYPE_SCHEDULED).text.strip()

    def scheduled_publish_type(self):
        return self.element(SignUpPage.PUBLISH_TYPE_SCHEDULED).text.strip()
