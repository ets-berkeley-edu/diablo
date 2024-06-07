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


class CoursePage(DiabloPages):

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

    CC_EXPLAINED_LINK = (By.ID, 'link-to-course-capture-overview')
    RECORDING_TYPE_TEXT = (By.XPATH, '//div[contains(text(), "\'Presentation and Audio\' recordings are free")]')
    PUBLISH_TYPE_TEXT = (By.XPATH, '//div[contains(text(), "If you choose \'GSI/TA moderation\'")]')
    RECORDING_TYPE_STATIC = (By.XPATH, '//input[@name="recordingType"]/..')
    SELECT_RECORDING_TYPE_INPUT = (By.XPATH, '//label[@id="select-recording-type-label"]')
    SELECT_PUBLISH_TYPE_INPUT = (By.XPATH, '//input[@id="select-publish-type"]/..')
    CC_POLICIES_LINK = (By.ID, 'link-to-course-capture-policies')
    APPROVE_BUTTON = (By.ID, 'btn-approve')
    QUEUED_MSG = (By.XPATH, '//span[contains(text(), "This course is currently queued for scheduling")]')
    APPROVALS_MSG = (By.ID, 'approvals-described')
    CONFIRMATION_MSG = (By.XPATH, '//span[contains(text(), "You submitted the preferences below.")]')
    NO_AUTO_SCHED_MSG = (By.XPATH, '//div[contains(text(), "cannot be scheduled automatically")]')
    NOT_ELIGIBLE_MSG = (By.ID, 'course-not-eligible')

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
        return meeting.meeting_schedule.expected_recording_dates(term)[-1].strftime('%b %-d, %Y')

    @staticmethod
    def kaltura_series_link(recording_schedule):
        return By.PARTIAL_LINK_TEXT, f'Kaltura series {recording_schedule.series_id}'

    def hit_url(self, term_id, ccn):
        self.driver.get(f'{app.config["BASE_URL"]}/course/{term_id}/{ccn}')

    def load_page(self, section):
        app.logger.info(f'Loading course page for term {section.term.id} section ID {section.ccn}')
        self.hit_url(section.term.id, section.ccn)
        self.wait_for_diablo_title(f'{section.code}, {section.number}')

    # SIS DATA

    def is_canceled(self):
        return self.is_present((By.XPATH, '//span[text()="UC Berkeley has canceled this section."]'))

    def visible_ccn(self):
        return self.element(CoursePage.SECTION_ID).text

    def visible_course_title(self):
        return self.element(CoursePage.COURSE_TITLE).text

    def visible_instructors(self):
        els = self.elements(CoursePage.INSTRUCTOR)
        return [el.text for el in els]

    def visible_proxies(self):
        els = self.elements(CoursePage.PROXY)
        return [el.text for el in els]

    def visible_meeting_days(self):
        els = self.elements(CoursePage.MEETING_DAYS)
        vis = [el.get_attribute('innerText').replace('Days of the week:', '').replace('Dates:', '').strip() for el in els]
        app.logger.info(f'Visible {vis}')
        return vis

    def visible_meeting_time(self):
        els = self.elements(CoursePage.MEETING_TIMES)
        return [el.get_attribute('innerText').replace('Start and end times:', '').strip() for el in els]

    def visible_rooms(self):
        els = self.elements(CoursePage.ROOMS)
        return [el.get_attribute('innerText').replace('Location:', '').strip() for el in els]

    def visible_course_site_ids(self):
        site_els = self.elements(CoursePage.COURSE_SITE_LINK)
        return [el.get_attribute('id').split('-')[-1] for el in site_els]

    def visible_cross_listing_codes(self):
        return [el.text for el in self.elements(CoursePage.CROSS_LISTING)]

    def visible_cross_listing_ccns(self):
        return [el.get_attribute('id').split('-')[2] for el in self.elements(CoursePage.CROSS_LISTING)]

    def visible_opt_out(self):
        return self.element(CoursePage.OPTED_OUT).get_attribute('innerText').strip()

    def click_room_link(self, room):
        self.wait_for_element_and_click(self.room_link_locator(room))

    # CAPTURE SETTINGS

    def click_rec_type_input(self):
        app.logger.info('Clicking the recording type input')
        self.wait_for_element_and_click(CoursePage.SELECT_RECORDING_TYPE_INPUT)

    def click_publish_type_input(self):
        app.logger.info('Clicking the publish type input')
        self.wait_for_element_and_click(CoursePage.SELECT_PUBLISH_TYPE_INPUT)

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

    # COLLABORATORS

    COLLAB_ROW = By.XPATH, '//div[contains(@id, "collaborator-")]'
    COLLAB_EDIT_BUTTON = By.ID, 'btn-collaborators-edit'
    COLLAB_NONE_MSG = By.ID, 'collaborators-none'
    COLLAB_INPUT = By.ID, 'input-collaborator-lookup-autocomplete'
    COLLAB_ADD_BUTTON = By.ID, 'btn-collaborator-add'
    COLLAB_SAVE_BUTTON = By.ID, 'btn-collaborators-save'
    COLLAB_CXL_BUTTON = By.ID, 'btn-recording-type-cancel'

    @staticmethod
    def collaborator_row_loc(user):
        return By.ID, f'collaborator-{user.uid}'

    def is_collaborator_present(self, user):
        return self.is_present(self.collaborator_row_loc(user))

    def visible_collaborator_uids(self):
        return list(map(lambda el: el.get_attribute('id').split('-')[-1], self.elements(self.COLLAB_ROW)))

    def click_edit_collaborators(self):
        app.logger.info('Clicking the edit collaborators button')
        self.wait_for_element_and_click(self.COLLAB_EDIT_BUTTON)

    # Adding

    def look_up_uid(self, uid):
        app.logger.info(f'Looking up UID {uid}')
        self.remove_and_enter_chars(self.COLLAB_INPUT, uid)

    def look_up_email(self, email):
        app.logger.info(f'Looking up {email}')
        self.remove_and_enter_chars(self.COLLAB_INPUT, email)

    @staticmethod
    def add_collaborator_lookup_result(user):
        return By.XPATH, f'//div[contains(@id, "list-item")][contains(., "({user.uid})")]'

    def click_look_up_result(self, user):
        self.wait_for_page_and_click(self.add_collaborator_lookup_result(user))

    def click_collaborator_add_button(self):
        self.wait_for_element_and_click(self.COLLAB_ADD_BUTTON)

    def add_collaborator_by_uid(self, user):
        self.look_up_uid(user.uid)
        self.click_look_up_result(user)
        self.click_collaborator_add_button()

    def add_collaborator_by_email(self, user):
        self.look_up_email(user.email)
        self.click_look_up_result(user)
        self.click_collaborator_add_button()

    # Removing

    @staticmethod
    def remove_collaborator_button_loc(user):
        return By.ID, f'btn-collaborator-remove-{user.uid}'

    def click_remove_collaborator(self, user):
        self.wait_for_element_and_click(self.remove_collaborator_button_loc(user))

    # Save, Cancel

    def save_collaborator_edits(self):
        self.wait_for_element_and_click(self.COLLAB_SAVE_BUTTON)

    def cancel_collaborator_edits(self):
        self.wait_for_element_and_click(self.COLLAB_CXL_BUTTON)

    @staticmethod
    def collaborator_remove_button_loc(user):
        return By.ID, f'btn-collaborator-remove-{user.uid}'

    def click_approve_button(self):
        app.logger.info('Clicking the approve button')
        self.wait_for_element_and_click(CoursePage.APPROVE_BUTTON)

    # TODO - repurpose the following with new messaging

    def wait_for_queued_confirmation(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(CoursePage.QUEUED_MSG))

    def wait_for_approvals_msg(self, string=None):
        Wait(self.driver, util.get_medium_timeout()).until(ec.visibility_of_element_located(CoursePage.APPROVALS_MSG))
        if string:
            app.logger.info(f'Visible: {self.element(CoursePage.APPROVALS_MSG).get_attribute("innerText")}')
            self.wait_for_text_in_element(CoursePage.APPROVALS_MSG, string)

    def wait_for_approval_confirmation(self):
        Wait(self.driver, util.get_short_timeout()).until(ec.visibility_of_element_located(CoursePage.CONFIRMATION_MSG))

    def default_rec_type(self):
        return self.element(CoursePage.RECORDING_TYPE_STATIC).text.strip()

    def approved_rec_type(self):
        return self.element(CoursePage.RECORDING_TYPE_APPROVED).text.strip()

    def approved_publish_type(self):
        return self.element(CoursePage.PUBLISH_TYPE_APPROVED).text.strip()

    def scheduled_rec_type(self):
        return self.element(CoursePage.RECORDING_TYPE_SCHEDULED).text.strip()

    def scheduled_publish_type(self):
        return self.element(CoursePage.PUBLISH_TYPE_SCHEDULED).text.strip()

    def click_kaltura_series_link(self, recording_schedule):
        app.logger.info(f'Clicking the link to Kaltura series ID {recording_schedule.series_id}')
        self.wait_for_page_and_click(CoursePage.kaltura_series_link(recording_schedule))
        time.sleep(2)
        self.switch_to_last_window(self.window_handles())
