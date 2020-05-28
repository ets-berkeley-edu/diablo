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

from diablo.models.scheduled import Scheduled
from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.pages.calnet_page import CalNetPage
from xena.pages.page import Page
from xena.test_utils import util


class KalturaPage(Page):

    USERNAME_INPUT = (By.ID, 'Login-username')
    PASSWORD_INPUT = (By.ID, 'Login-password')
    LOG_IN_BUTTON = (By.ID, 'Login-login')
    LOG_OUT_LINK = (By.XPATH, '//a[contains(@href, "/user/logout")]')

    SERIES_TITLE = (By.ID, 'CreateEvent-eventTitle')
    SERIES_ORGANIZER = (By.ID, 'CreateEvent-eventOrganizer')
    SERIES_RECUR_DESC = (By.ID, 'CreateEvent-RecurrenceDescription')
    SERIES_RECUR_BUTTON = (By.ID, 'CreateEvent-recurrenceMain')
    SERIES_DELETE_BUTTON = (By.ID, 'CreateEvent-btnDelete')
    SERIES_DELETE_CONFIRM_BUTTON = (By.XPATH, '//div[@class="modal-footer"]/a[text()="Delete"]')

    RECUR_DESC = (By.ID, 'CreateEvent-RecurrenceDescription')
    RECUR_MODAL_H3 = (By.XPATH, '//h3[text()="Event Recurrence"]')
    RECUR_WEEKLY_RADIO = (By.ID, 'EventRecurrence-recurrence-weeks')
    RECUR_WEEKLY_FREQUENCY = (By.ID, 'EventRecurrence-weekly_index')
    RECUR_WEEKLY_MON_CBX = (By.ID, 'EventRecurrence-weekly_days-MO')
    RECUR_WEEKLY_TUE_CBX = (By.ID, 'EventRecurrence-weekly_days-TU')
    RECUR_WEEKLY_WED_CBX = (By.ID, 'EventRecurrence-weekly_days-WE')
    RECUR_WEEKLY_THU_CBX = (By.ID, 'EventRecurrence-weekly_days-TH')
    RECUR_WEEKLY_FRI_CBX = (By.ID, 'EventRecurrence-weekly_days-FR')
    RECUR_WEEKLY_SAT_CBX = (By.ID, 'EventRecurrence-weekly_days-SA')
    RECUR_WEEKLY_SUN_CBX = (By.ID, 'EventRecurrence-weekly_days-SU')
    RECUR_DATE_START = (By.ID, 'EventRecurrence-start')
    RECUR_DATE_END = (By.ID, 'EventRecurrence-endby_date')
    RECUR_TIME_START = (By.ID, 'EventRecurrence-startTime')
    RECUR_TIME_END = (By.ID, 'EventRecurrence-endTime')
    RECUR_MODAL_CANCEL_BUTTON = (By.LINK_TEXT, 'Cancel')

    def log_in(self):
        app.logger.info('Logging in to Kaltura')
        self.driver.get(f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/user/login')
        self.wait_for_element_and_type(KalturaPage.USERNAME_INPUT, app.config['XENA_KALTURA_USERNAME'])
        self.wait_for_element_and_type(KalturaPage.PASSWORD_INPUT, app.config['XENA_KALTURA_PASSWORD'])
        self.wait_for_element_and_click(KalturaPage.LOG_IN_BUTTON)
        Wait(self.driver, util.get_short_timeout()).until(ec.presence_of_element_located(KalturaPage.LOG_OUT_LINK))

    def log_in_via_calnet(self):
        app.logger.info('Logging in to Kaltura')
        self.driver.get(f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/user/login')
        self.wait_for_element_and_type(CalNetPage.USERNAME_INPUT, 'PLEASE LOG IN MANUALLY')
        Wait(self.driver, util.get_long_timeout()).until(ec.presence_of_element_located(KalturaPage.LOG_OUT_LINK))

    def load_event_edit_page(self, recording_schedule):
        self.driver.get(f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/recscheduling/index/edit-event/eventid/{recording_schedule.series_id}')

    def wait_for_delete_button(self):
        self.wait_for_element(KalturaPage.SERIES_DELETE_BUTTON, util.get_short_timeout())

    def selected_resource_el(self, room):
        return self.element((By.XPATH, f'//span[@id="{room.resource_id}"][text()="{room.name}"]'))

    def open_recurrence_modal(self):
        app.logger.info('Clicking recurrence button')
        self.wait_for_element_and_click(KalturaPage.SERIES_RECUR_BUTTON)
        self.wait_for_element(KalturaPage.RECUR_MODAL_H3, util.get_short_timeout())

    def visible_series_title(self):
        return self.element(KalturaPage.SERIES_TITLE).get_attribute('value')

    def visible_series_organizer(self):
        return self.element(KalturaPage.SERIES_ORGANIZER).get_attribute('value')

    def visible_recurrence_desc(self):
        return self.element(KalturaPage.RECUR_DESC).text

    def is_weekly_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_RADIO).is_selected()

    def visible_weekly_frequency(self):
        return self.element(KalturaPage.RECUR_WEEKLY_FREQUENCY).get_attribute('value')

    def is_mon_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_MON_CBX).is_selected()

    def is_tue_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_TUE_CBX).is_selected()

    def is_wed_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_WED_CBX).is_selected()

    def is_thu_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_THU_CBX).is_selected()

    def is_fri_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_FRI_CBX).is_selected()

    def is_sat_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_SAT_CBX).is_selected()

    def is_sun_checked(self):
        return self.element(KalturaPage.RECUR_WEEKLY_SUN_CBX).is_selected()

    def visible_start_date(self):
        return self.element(KalturaPage.RECUR_DATE_START).get_attribute('value')

    def visible_end_date(self):
        return self.element(KalturaPage.RECUR_DATE_END).get_attribute('value')

    def visible_start_time(self):
        return self.element(KalturaPage.RECUR_TIME_START).get_attribute('value')

    def visible_end_time(self):
        return self.element(KalturaPage.RECUR_TIME_END).get_attribute('value')

    # DELETION

    def reset_test_data(self, term, recording_schedule):
        old_schedule = Scheduled.get_scheduled(recording_schedule.section.ccn, term.id)
        if old_schedule:
            recording_schedule.series_id = old_schedule.kaltura_schedule_id
            app.logger.info(f'Deleting an existing Kaltura series id {recording_schedule.series_id}')
            self.delete_series(recording_schedule)
        else:
            app.logger.info('Cannot find any existing Kaltura series')

    def delete_series(self, recording_schedule):
        app.logger.info('Clicking the delete button')
        self.load_event_edit_page(recording_schedule)
        self.wait_for_page_and_click(KalturaPage.SERIES_DELETE_BUTTON)
        self.wait_for_element_and_click(KalturaPage.SERIES_DELETE_CONFIRM_BUTTON)
        redirect_url = f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/calendar/index/calendar/'
        Wait(self.driver, util.get_short_timeout()).until(ec.url_to_be(redirect_url))
