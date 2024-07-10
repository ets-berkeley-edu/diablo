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
from datetime import datetime
import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.models.recording_placement import RecordingPlacement
from xena.pages.page import Page
from xena.test_utils import util


class KalturaPage(Page):

    USERNAME_INPUT = (By.ID, 'Login-username')
    PASSWORD_INPUT = (By.ID, 'Login-password')
    LOG_IN_BUTTON = (By.ID, 'Login-login')
    LOG_OUT_LINK = (By.XPATH, '//a[contains(@href, "/user/logout")]')

    SERIES_TITLE = (By.ID, 'CreateEvent-eventTitle')
    SERIES_DESC = (By.ID, 'CreateEvent-eventDescription')
    SERIES_ORGANIZER = (By.ID, 'CreateEvent-eventOrganizer')
    SERIES_RECUR_DESC = (By.ID, 'CreateEvent-RecurrenceDescription')
    SERIES_COLLABORATOR_ROW = (By.XPATH, '//tr[contains(@id, "collaborator_")]')
    SERIES_STATUS_PRIVATE_RADIO = (By.ID, 'private_upload1')
    SERIES_STATUS_PUBLISHED_RADIO = (By.ID, 'published_upload1')
    SERIES_PUBLICATION_CHANNELS = (By.ID, 'pblPublish_upload1')
    SERIES_CATEGORY_ROW = (By.XPATH, '//div[@class="pblBadge"]/dl//span')
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

    def log_in_via_calnet(self, calnet_page):
        app.logger.info('Logging in to Kaltura')
        self.driver.get(f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/user/login')
        username = util.get_username()
        password = util.get_password()
        if self.is_present(KalturaPage.LOG_OUT_LINK):
            app.logger.info('User is already logged in to Kaltura')
        else:
            calnet_page.log_in(username, password)
            Wait(self.driver, util.get_medium_timeout()).until(ec.presence_of_element_located(KalturaPage.LOG_OUT_LINK))

    def load_event_edit_page(self, series_id):
        app.logger.info(f'Loading Kaltura series {series_id}')
        self.driver.get(f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/recscheduling/index/edit-event/eventid/{series_id}')

    def wait_for_delete_button(self):
        self.wait_for_element(KalturaPage.SERIES_DELETE_BUTTON, util.get_short_timeout())

    def selected_resource_el(self, room):
        return self.element((By.XPATH, f'//span[@id="{room.resource_id}"][text()="{room.name}"]'))

    def collaborator_rows(self):
        return self.elements(KalturaPage.SERIES_COLLABORATOR_ROW)

    def collaborator_perm(self, user):
        return self.element((By.XPATH, f'//tr[@id="collaborator_{user.uid}"]/td[3]')).text.strip()

    def wait_for_publish_category_el(self):
        self.wait_for_element(KalturaPage.SERIES_CATEGORY_ROW, util.get_medium_timeout())

    def is_private(self):
        return self.element(self.SERIES_PUBLICATION_CHANNELS).get_attribute('class') == 'hidden'

    def is_published(self):
        return self.element(self.SERIES_PUBLICATION_CHANNELS).get_attribute('class') != 'hidden'

    def publish_category_els(self):
        return self.elements(KalturaPage.SERIES_CATEGORY_ROW)

    def is_publish_category_present(self, site):
        return self.is_present((By.XPATH, f'//div[@class="pblBadge"][contains(., "{site.code}")]'))

    def open_recurrence_modal(self):
        app.logger.info('Clicking recurrence button')
        self.wait_for_element_and_click(KalturaPage.SERIES_RECUR_BUTTON)
        self.wait_for_element(KalturaPage.RECUR_MODAL_H3, util.get_medium_timeout())

    def close_recurrence_modal(self):
        app.logger.info('Closing recurrence modal')
        self.wait_for_element_and_click(KalturaPage.RECUR_MODAL_CANCEL_BUTTON)
        self.when_not_present(KalturaPage.RECUR_MODAL_CANCEL_BUTTON, util.get_short_timeout())

    def visible_series_title(self):
        return self.element(KalturaPage.SERIES_TITLE).get_attribute('value')

    def visible_series_desc(self):
        return self.element(KalturaPage.SERIES_DESC).text

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

    def verify_recur_days(self, days):
        assert self.is_mon_checked() if 'MO' in days else not self.is_mon_checked()
        assert self.is_tue_checked() if 'TU' in days else not self.is_tue_checked()
        assert self.is_wed_checked() if 'WE' in days else not self.is_wed_checked()
        assert self.is_thu_checked() if 'TH' in days else not self.is_thu_checked()
        assert self.is_fri_checked() if 'FR' in days else not self.is_fri_checked()
        assert not self.is_sat_checked()
        assert not self.is_sun_checked()

    def visible_start_date(self):
        return self.element(KalturaPage.RECUR_DATE_START).get_attribute('value')

    def visible_end_date(self):
        return self.element(KalturaPage.RECUR_DATE_END).get_attribute('value')

    def visible_start_time(self):
        return self.element(KalturaPage.RECUR_TIME_START).get_attribute('value')

    def visible_end_time(self):
        return self.element(KalturaPage.RECUR_TIME_END).get_attribute('value')

    # DELETION

    def reset_test_data(self, section):
        series_ids = util.get_kaltura_ids(section)
        for series_id in series_ids:
            app.logger.info(f'Deleting an existing Kaltura series {series_id}')
            self.delete_series(series_id)
        else:
            app.logger.info('Cannot find any existing Kaltura series')

    def delete_series(self, series_id):
        app.logger.info('Clicking the delete button')
        self.load_event_edit_page(series_id)
        self.wait_for_element(KalturaPage.SERIES_DELETE_BUTTON, util.get_medium_timeout())
        self.scroll_to_bottom()
        self.wait_for_page_and_click(KalturaPage.SERIES_DELETE_BUTTON, 3)
        self.wait_for_element_and_click(KalturaPage.SERIES_DELETE_CONFIRM_BUTTON)
        redirect_url = f'{app.config["KALTURA_MEDIA_SPACE_URL"]}/calendar/index/calendar/'
        Wait(self.driver, util.get_short_timeout()).until(ec.url_to_be(redirect_url))

    # ACTUAL VS EXPECTED

    def verify_title_and_desc(self, section, meeting):
        self.wait_for_delete_button()
        expected = f'{section.code}, {section.number} ({section.term.name})'
        assert self.visible_series_title() == expected

        instructors = []
        for instr in section.instructors:
            instructors.append(f'{instr.first_name} {instr.last_name}'.strip())
        instructors = ' and '.join(instructors)
        course = f'{section.code}, {section.number} ({section.term.name})'
        copy = f"Copyright ©{datetime.strftime(meeting.meeting_schedule.start_date, '%Y')} UC Regents; all rights reserved."
        expected = f'{course} is taught by {instructors}. {copy}'
        app.logger.info(f'Expecting {expected}, got {self.visible_series_desc()}')
        assert self.visible_series_desc() == expected

    def verify_collaborators(self, section, addl_collaborators=None):
        self.wait_for_delete_button()
        all_collabs = []
        all_collabs.extend(section.instructors)
        if addl_collaborators:
            all_collabs.extend(addl_collaborators)
        for collab in all_collabs:
            app.logger.info(f'Verifying collaborator UID {collab.uid} perms')
            assert self.collaborator_perm(collab) == 'Co-Editor, Co-Publisher'
        app.logger.info(f'Expecting {len(all_collabs)} collaborators, got {len(self.collaborator_rows())}')
        assert len(self.collaborator_rows()) == len(all_collabs)

    def verify_schedule(self, section, meeting):
        self.wait_for_delete_button()
        schedule = meeting.meeting_schedule
        self.open_recurrence_modal()
        assert self.is_weekly_checked()
        assert self.visible_weekly_frequency() == '1'

        self.verify_recur_days(schedule.days)

        start = util.get_kaltura_term_date_str(schedule.expected_recording_dates(section.term)[0])
        assert self.visible_start_date() == start

        end = util.get_kaltura_term_date_str(schedule.expected_recording_dates(section.term)[-1])
        assert self.visible_end_date() == end

        start = schedule.get_berkeley_start_time()
        visible_start = datetime.strptime(self.visible_start_time(), '%I:%M %p')
        assert visible_start == start

        end = schedule.get_berkeley_end_time()
        visible_end = datetime.strptime(self.visible_end_time(), '%I:%M %p')
        assert visible_end == end

    def verify_publish_status(self, recording_schedule):
        self.wait_for_delete_button()
        self.wait_for_element(self.SERIES_PUBLICATION_CHANNELS, util.get_short_timeout())
        time.sleep(3)

        app.logger.info(f"Pub channels el class is {self.element(self.SERIES_PUBLICATION_CHANNELS).get_attribute('class')}")

        if recording_schedule.recording_placement == RecordingPlacement.PUBLISH_TO_MY_MEDIA:
            assert self.is_private()
        elif recording_schedule.recording_placement == RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY:
            assert self.is_published()

    def verify_site_categories(self, sites):
        expected_count = len(sites) * 2
        self.wait_for_delete_button()
        self.scroll_to_bottom()
        if expected_count > 0:
            self.wait_for_element(self.SERIES_CATEGORY_ROW, util.get_short_timeout())
        else:
            self.wait_for_element(self.SERIES_PUBLICATION_CHANNELS, util.get_short_timeout())
        visible_count = len(self.publish_category_els())
        if visible_count != expected_count:
            app.logger.info(f'Expected {expected_count} categories, got {visible_count}')
        assert visible_count == expected_count

        expected_ids = list(map(lambda site: site.site_id, sites))
        expected_ids.sort()
        visible_ids = list(map(lambda el: el.text, self.publish_category_els()))
        visible_ids = list(set(visible_ids))
        visible_ids.sort()
        if visible_ids != expected_ids:
            app.logger.info(f'Expected site IDs {expected_ids}, got {visible_ids}')
        assert visible_ids == expected_ids
