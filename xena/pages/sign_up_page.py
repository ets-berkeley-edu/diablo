"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class SignUpPage(DiabloPages):

    SECTION_ID = (By.ID, 'section-id')
    COURSE_TITLE = (By.ID, 'course-title')
    INSTRUCTORS = (By.ID, 'instructors')
    INSTRUCTOR = (By.XPATH, '//*[contains(@id, "instructor-")][not(contains(@id, "proxy"))]')
    PROXY = (By.XPATH, '//span[contains(@id, "instructor-proxy-")]')
    MEETING_DAYS = (By.XPATH, '//*[contains(@id, "meeting-days-")]')
    MEETING_TIMES = (By.XPATH, '//*[contains(@id, "meeting-times-")]')
    ROOMS = (By.XPATH, '//*[contains(@id, "rooms-")]')
    COURSE_SITE_LINK = (By.XPATH, '//a[contains(@id, "canvas-course-site-")]')
    CROSS_LISTING = (By.XPATH, '//div[contains(@id, "cross-listing-")]')
    OPTED_OUT = (By.ID, 'opted-out')
    SEND_INVITE_BUTTON = (By.ID, 'send-invite-btn')
    UNSCHEDULE_BUTTON = (By.ID, 'unschedule-course-btn')
    UNSCHEDULE_CONFIRM_BUTTON = (By.ID, 'confirm-unschedule-course-btn')
    UNSCHEDULE_CANCEL_BUTTON = (By.ID, 'cancel-unschedule-course-btn')

    CC_EXPLAINED_LINK = (By.ID, 'link-to-course-capture-overview')
    RECORDING_TYPE_TEXT = (By.XPATH, '//div[contains(text(), "\'Presentation and Audio\' recordings are free")]')
    PUBLISH_TYPE_TEXT = (By.XPATH, '//div[contains(text(), "If you choose \'GSI/TA moderation\'")]')
    RECORDING_TYPE_STATIC = (By.XPATH, '//input[@name="recordingType"]/..')
    SELECT_RECORDING_TYPE_INPUT = (By.XPATH, '//label[@id="select-recording-type-label"]')
    SELECT_PUBLISH_TYPE_INPUT = (By.XPATH, '//input[@id="select-publish-type"]/..')
    AGREE_TO_TERMS_CBX = (By.XPATH, '//input[@id="agree-to-terms-checkbox"]/..')
    APRX_CAN_EDIT_CBX = (By.ID, 'can-aprx-instructors-edit-recordings')
    CC_POLICIES_LINK = (By.ID, 'link-to-course-capture-policies')
    APPROVE_BUTTON = (By.ID, 'btn-approve')
    QUEUED_MSG = (By.XPATH, '//span[contains(text(), "This course is currently queued for scheduling")]')
    APPROVALS_MSG = (By.ID, 'approvals-described')
    CONFIRMATION_MSG = (By.XPATH, '//span[contains(text(), "You submitted the preferences below.")]')
    NO_AUTO_SCHED_MSG = (By.XPATH, '//div[contains(text(), "cannot be scheduled automatically")]')
    NOT_ELIGIBLE_MSG = (By.ID, 'course-not-eligible')

    APRX_CAN_EDIT_FLAG = (By.ID, 'admin-proxy-status')

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

    @staticmethod
    def course_site_link_locator(site):
        return By.XPATH, f'//a[@id="canvas-course-site-{site.site_id}"]'

    @staticmethod
    def not_authorized_msg_locator(section):
        return By.XPATH, f'//span[contains(text(), "Sorry, you are unauthorized to view the course {section.code}, {section.number}")]'

    @staticmethod
    def expected_term_date_str(start_date, end_date):
        start_str = start_date.strftime('%b %-d, %Y')
        end_str = end_date.strftime('%b %-d, %Y')
        return f'{start_str} to {end_str}'

    @staticmethod
    def expected_final_record_date_str(meeting, term):
        return meeting.expected_recording_dates(term)[-1].strftime('%b %-d, %Y')

    @staticmethod
    def kaltura_series_link(recording_schedule):
        return By.PARTIAL_LINK_TEXT, f'Kaltura series {recording_schedule.series_id}'

    def hit_url(self, term_id, ccn):
        self.driver.get(f'{app.config["BASE_URL"]}/course/{term_id}/{ccn}')

    def load_page(self, section):
        app.logger.info(f'Loading sign-up page for term {section.term.id} section ID {section.ccn}')
        self.hit_url(section.term.id, section.ccn)
        self.wait_for_diablo_title(f'{section.code}, {section.number}')

    # SIS DATA

    def is_canceled(self):
        return self.is_present((By.XPATH, '//span[text()="UC Berkeley has canceled this section."]'))

    def visible_ccn(self):
        return self.element(SignUpPage.SECTION_ID).text

    def visible_course_title(self):
        return self.element(SignUpPage.COURSE_TITLE).text

    def visible_instructors(self):
        els = self.elements(SignUpPage.INSTRUCTOR)
        return [el.text for el in els]

    def visible_proxies(self):
        els = self.elements(SignUpPage.PROXY)
        return [el.text for el in els]

    def visible_meeting_days(self):
        els = self.elements(SignUpPage.MEETING_DAYS)
        vis = [el.get_attribute('innerText').replace('Days of the week:', '').replace('Dates:', '').strip() for el in els]
        app.logger.info(f'Visible {vis}')
        return vis

    def visible_meeting_time(self):
        els = self.elements(SignUpPage.MEETING_TIMES)
        return [el.get_attribute('innerText').replace('Start and end times:', '').strip() for el in els]

    def visible_rooms(self):
        els = self.elements(SignUpPage.ROOMS)
        return [el.get_attribute('innerText').replace('Location:', '').strip() for el in els]

    def visible_course_site_ids(self):
        site_els = self.elements(SignUpPage.COURSE_SITE_LINK)
        return [el.get_attribute('id').split('-')[-1] for el in site_els]

    def visible_cross_listing_codes(self):
        return [el.text for el in self.elements(SignUpPage.CROSS_LISTING)]

    def visible_cross_listing_ccns(self):
        return [el.get_attribute('id').split('-')[2] for el in self.elements(SignUpPage.CROSS_LISTING)]

    def visible_opt_out(self):
        return self.element(SignUpPage.OPTED_OUT).get_attribute('innerText').strip()

    def click_room_link(self, room):
        self.wait_for_element_and_click(self.room_link_locator(room))

    # INVITES, UN-SCHEDULING, OPTED-OUT

    def click_send_invite_button(self):
        app.logger.info('Clicking the Send Invite button')
        self.wait_for_element_and_click(SignUpPage.SEND_INVITE_BUTTON)
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(SignUpPage.ALERT_MSG))

    def click_unschedule_button(self):
        app.logger.info('Clicking the Unschedule button')
        self.wait_for_element_and_click(SignUpPage.UNSCHEDULE_BUTTON)

    def confirm_unscheduling(self, recording_schedule):
        self.click_unschedule_button()
        self.wait_for_element_and_click(SignUpPage.UNSCHEDULE_CONFIRM_BUTTON)
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(SignUpPage.APPROVE_BUTTON))
        recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def confirm_unscheduling_ineligible(self, recording_schedule):
        self.click_unschedule_button()
        self.wait_for_element_and_click(SignUpPage.UNSCHEDULE_CONFIRM_BUTTON)
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(SignUpPage.OPTED_OUT))
        recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED
        time.sleep(util.get_short_timeout())

    def cancel_unscheduling(self):
        self.click_unschedule_button()
        self.wait_for_element_and_click(SignUpPage.UNSCHEDULE_CANCEL_BUTTON)
        Wait(self.driver, 1).until(ec.invisibility_of_element_located(SignUpPage.UNSCHEDULE_CANCEL_BUTTON))

    def is_opted_out(self):
        return self.is_present(SignUpPage.OPTED_OUT)

    # CAPTURE + APPROVAL SETTINGS

    def instructor_approval_present(self, instructor):
        locator = (By.XPATH, f'//div[contains(text(), "{instructor.first_name} {instructor.last_name}")][contains(., "approved.")]')
        return self.is_present(locator)

    def admin_approval_present(self):
        locator = (By.XPATH, '//span[text()="(Course Capture administrator)"]/..[contains(., "approved.")]')
        return self.is_present(locator)

    def click_rec_type_input(self):
        app.logger.info('Clicking the recording type input')
        self.wait_for_element_and_click(SignUpPage.SELECT_RECORDING_TYPE_INPUT)

    def click_publish_type_input(self):
        app.logger.info('Clicking the publish type input')
        self.wait_for_element_and_click(SignUpPage.SELECT_PUBLISH_TYPE_INPUT)

    def select_rec_type(self, recording_type):
        app.logger.info(f'Selecting recording type {recording_type}')
        self.hit_escape()
        self.click_rec_type_input()
        self.click_menu_option(recording_type)

    def select_publish_type(self, publish_type):
        app.logger.info(f'Selecting publish type {publish_type}')
        self.hit_escape()
        self.click_publish_type_input()
        self.click_menu_option(publish_type)

    def click_agree_checkbox(self):
        app.logger.info('Clicking the agree-to-terms checkbox')
        self.wait_for_element_and_click(SignUpPage.AGREE_TO_TERMS_CBX)

    def aprx_editor_checked(self):
        return self.element(SignUpPage.APRX_CAN_EDIT_CBX).get_attribute('aria-checked') == 'true'

    def select_aprx_editor(self):
        if not self.aprx_editor_checked():
            self.click_element_js(SignUpPage.APRX_CAN_EDIT_CBX)

    def deselect_aprx_editor(self):
        if self.aprx_editor_checked():
            self.click_element_js(SignUpPage.APRX_CAN_EDIT_CBX)

    def click_approve_button(self):
        app.logger.info('Clicking the approve button')
        self.wait_for_element_and_click(SignUpPage.APPROVE_BUTTON)

    def wait_for_queued_confirmation(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(SignUpPage.QUEUED_MSG))

    def wait_for_approvals_msg(self, string=None):
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(SignUpPage.APPROVALS_MSG))
        if string:
            app.logger.info(f'Visible: {self.element(SignUpPage.APPROVALS_MSG).get_attribute("innerText")}')
            self.wait_for_text_in_element(SignUpPage.APPROVALS_MSG, string)

    def wait_for_approval_confirmation(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(SignUpPage.CONFIRMATION_MSG))

    def default_rec_type(self):
        return self.element(SignUpPage.RECORDING_TYPE_STATIC).text.strip()

    def aprx_can_edit_flag(self):
        return self.element(SignUpPage.APRX_CAN_EDIT_FLAG).text.strip()

    def approved_rec_type(self):
        return self.element(SignUpPage.RECORDING_TYPE_APPROVED).text.strip()

    def approved_publish_type(self):
        return self.element(SignUpPage.PUBLISH_TYPE_APPROVED).text.strip()

    def scheduled_rec_type(self):
        return self.element(SignUpPage.RECORDING_TYPE_SCHEDULED).text.strip()

    def scheduled_publish_type(self):
        return self.element(SignUpPage.PUBLISH_TYPE_SCHEDULED).text.strip()

    def click_kaltura_series_link(self, recording_schedule):
        app.logger.info(f'Clicking the link to Kaltura series ID {recording_schedule.series_id}')
        self.wait_for_page_and_click(SignUpPage.kaltura_series_link(recording_schedule))
        time.sleep(2)
        self.switch_to_last_window(self.window_handles())
