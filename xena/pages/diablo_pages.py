"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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
import re
from datetime import datetime, time, timezone
from time import sleep

from flask import current_app as app
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait

from diablo.lib.i_cal import get_kaltura_safe_name
from diablo.lib.util import default_timezone
from xena.pages.page import Page
from xena.test_utils import util


class DiabloPages(Page):

    OUIJA_BOARD_LINK = (By.ID, 'sidebar-link-ouija-board')
    ROOMS_LINK = (By.ID, 'sidebar-link-rooms')
    BLACKOUTS_LINK = (By.ID, 'sidebar-link-blackouts')
    EMAIL_TEMPLATES_LINK = (By.ID, 'sidebar-link-email-templates')
    JOBS_LINK = (By.ID, 'sidebar-link-the-chancel')

    MENU_BUTTON = (By.ID, 'btn-main-menu')
    DARK_MODE = (By.ID, 'menu-item-dark-mode"]')
    LOG_OUT_LINK = (By.ID, 'menu-item-log-out')

    SPINNER = (By.XPATH, '//div[contains(@class, "spinner")]')
    ALERT_MSG = (By.ID, 'alert-text')
    VISIBLE_MENU_OPTION = (By.XPATH, '//div[@role="option"]')

    @staticmethod
    def menu_option_locator(option_str):
        return By.XPATH, f'//div[contains(@class, "v-list-item")][contains(., "{option_str}")]'

    def wait_for_diablo_title(self, string):
        self.wait_for_title(f'{string} | Course Capture')

    def click_ouija_board_link(self):
        app.logger.info('Clicking Ouija Board link')
        self.wait_for_element_and_click(DiabloPages.OUIJA_BOARD_LINK)

    def click_rooms_link(self):
        app.logger.info('Clicking Rooms link')
        self.wait_for_element_and_click(DiabloPages.ROOMS_LINK)

    def click_blackouts_link(self):
        app.logger.info('Clicking Blackouts link')
        self.wait_for_page_and_click(DiabloPages.BLACKOUTS_LINK)

    def click_email_templates_link(self):
        app.logger.info('Clicking Email Templates link')
        self.wait_for_element_and_click(DiabloPages.EMAIL_TEMPLATES_LINK)

    def click_jobs_link(self):
        app.logger.info("Clicking 'The Chancel' link")
        sleep(2)
        self.wait_for_element_and_click(DiabloPages.JOBS_LINK)
        sleep(1)
        self.mouseover(self.element(DiabloPages.MENU_BUTTON))

    def click_menu_button(self, locator):
        self.wait_for_page_and_click_js(locator)

    def open_menu(self, button_locator, content_locator, name):
        if not self.is_visible(content_locator):
            app.logger.info(f'Clicking {name} menu button')
            self.click_menu_button(button_locator)
            sleep(1)
        if not self.is_visible(content_locator):
            app.logger.info('Retrying the menu button')
            self.click_menu_button(button_locator)

    def log_out(self):
        app.logger.info('Logging out')
        self.open_menu(DiabloPages.MENU_BUTTON, DiabloPages.LOG_OUT_LINK, 'header')
        self.wait_for_page_and_click(DiabloPages.LOG_OUT_LINK)
        # Logging out is not working the first time in some cases, retry for now
        sleep(2)
        if self.is_present(DiabloPages.LOG_OUT_LINK):
            self.open_menu(DiabloPages.MENU_BUTTON, DiabloPages.LOG_OUT_LINK, 'header')
            self.wait_for_page_and_click(DiabloPages.LOG_OUT_LINK)

    def click_menu_option(self, option_text):
        app.logger.info(f"Clicking the option '{option_text}'")
        self.wait_for_element_and_click(DiabloPages.menu_option_locator(option_text))

    def is_menu_option_disabled(self, option_text):
        return 'v-list-item--disabled' in self.element(DiabloPages.menu_option_locator(option_text)).get_dom_attribute('class')

    def visible_menu_options(self):
        Wait(self.driver, app.config['TIMEOUT_SHORT']).until(
            method=ec.visibility_of_any_elements_located(DiabloPages.VISIBLE_MENU_OPTION),
            message=f'Failed visible_menu_options: {DiabloPages.VISIBLE_MENU_OPTION}',
        )
        return [el.text for el in self.elements(DiabloPages.VISIBLE_MENU_OPTION)]

    # 404 PAGE

    def wait_for_404(self):
        Wait(self.driver, util.get_medium_timeout()).until(ec.url_contains('404'))

    # NOTES

    EDIT_NOTE_BUTTON = By.ID, 'btn-edit-note'
    SAVE_NOTE_BUTTON = By.ID, 'btn-save-note'
    CXL_NOTE_BUTTON = By.ID, 'btn-cancel-note'
    DELETE_NOTE_BUTTON = By.ID, 'btn-delete-note'
    NOTE_BODY = By.ID, 'note-body'
    NOTE_TEXT_AREA = By.ID, 'note-body-edit'

    def click_edit_note(self):
        self.wait_for_element_and_click(self.EDIT_NOTE_BUTTON)

    def click_save_note(self):
        self.wait_for_element_and_click(self.SAVE_NOTE_BUTTON)

    def click_cancel_note(self):
        self.wait_for_element_and_click(self.CXL_NOTE_BUTTON)

    def click_delete_note(self):
        self.wait_for_element_and_click(self.DELETE_NOTE_BUTTON)

    def enter_note_body(self, string):
        self.wait_for_element(self.NOTE_TEXT_AREA, util.get_short_timeout())
        self.remove_and_enter_chars(self.NOTE_TEXT_AREA, string)

    def edit_note(self, string):
        self.click_edit_note()
        self.enter_note_body(string)
        self.click_save_note()

    def note_text(self):
        self.wait_for_element(self.NOTE_BODY, util.get_short_timeout())
        return self.element(self.NOTE_BODY).text.strip()

    def delete_note(self):
        self.click_delete_note()
        sleep(1)

    # ICAL EVENTS EXPORT

    EVENTS_EXPORT_BUTTON = (By.ID, 'kaltura-events-export-menu-btn')
    EVENTS_START_DATE_INPUT = (By.ID, 'kaltura-events-export-start-input')
    EVENTS_START_DATE_CLEAR_BUTTON = (By.ID, 'kaltura-events-export-start-clear-btn')
    EVENTS_END_DATE_INPUT = (By.ID, 'kaltura-events-export-end-input')
    EVENTS_END_DATE_CLEAR_BUTTON = (By.ID, 'kaltura-events-export-end-clear-btn')
    EVENTS_EXPORT_DOWNLOAD_BUTTON = (By.ID, 'kaltura-events-export-submit-btn')
    EVENTS_EXPORT_ERROR_MESSAGE = (By.ID, 'kaltura-events-export-error')

    def export_schedule_events_to_ical(self, events_start_date, events_end_date):
        # Make sure a clean download directory exists
        util.create_download_directory()

        # Click Export Events to iCal button
        self.open_menu(self.EVENTS_EXPORT_BUTTON, self.EVENTS_START_DATE_INPUT, 'Export Events to iCal')

        # If field is dirty, click the Clear button
        self.when_present(self.EVENTS_END_DATE_INPUT, util.get_short_timeout())
        if self.is_present(self.EVENTS_END_DATE_CLEAR_BUTTON):
            app.logger.info('Clicking clear button on end date input')
            self.wait_for_element_and_click(self.EVENTS_END_DATE_CLEAR_BUTTON)
        if self.is_present(self.EVENTS_START_DATE_CLEAR_BUTTON):
            app.logger.info('Clicking clear button on start date input')
            self.wait_for_element_and_click(self.EVENTS_START_DATE_CLEAR_BUTTON)

        start_date_str = events_start_date.strftime('%m/%d/%Y')
        end_date_str = events_end_date.strftime('%m/%d/%Y')
        app.logger.info(f'Entering date range {start_date_str} - {end_date_str}')
        self.wait_for_textbox_and_send_keys(self.EVENTS_START_DATE_INPUT, start_date_str, addl_pause=1)
        self.wait_for_textbox_and_send_keys(self.EVENTS_END_DATE_INPUT, end_date_str, addl_pause=1)
        sleep(1)

        self.when_present(self.EVENTS_EXPORT_DOWNLOAD_BUTTON, util.get_short_timeout())
        if self.element(self.EVENTS_EXPORT_DOWNLOAD_BUTTON).get_dom_attribute('disabled'):
            raise AssertionError('Events export download button is disabled')
        self.click_element(self.EVENTS_EXPORT_DOWNLOAD_BUTTON)

    def verify_ical_export_error(self, location='any eligible room'):
        error_message = f'No Kaltura events found for {location} between the specified dates.'
        app.logger.info(f'Waiting for error message "{error_message}"')
        self.wait_for_text_in_element(self.EVENTS_EXPORT_ERROR_MESSAGE, error_message, util.get_medium_timeout())

    def verify_ical_export_manifest(self, zip_file):
        app.logger.info('Parsing manifest of exported events')
        manifest = next((name for name in zip_file.namelist() if name == '_manifest.txt'), None)
        assert manifest

        digits_pattern = re.compile(r'(\d+)')
        manifest_path = zip_file.extract(manifest, util.default_download_dir())
        with open(manifest_path) as manifest_file:
            # First line contains count of rooms and total events; second line is blank
            totals_line = manifest_file.readline()
            assert len(totals_line)
            assert manifest_file.readline() == '\n'

            totals = digits_pattern.findall(totals_line)
            total_events_expected = totals[0]
            total_rooms = totals[1]
            total_events_actual = 0
            for i in range(int(total_rooms)):
                line = manifest_file.readline()
                events_count = digits_pattern.findall(line)[-1]
                total_events_actual += int(events_count)
            assert total_events_actual == int(total_events_expected)

            # Verify there are no more lines in the file
            assert not manifest_file.readline()

    def verify_ical_export_events(self, file_path, start_date, end_date, recording_sched=None):
        app.logger.info(f'Parsing Kaltura events .ics file {file_path}')
        events = []
        with open(file_path) as ics_file:
            for index, line in enumerate(ics_file):
                if index < 7:
                    # first 7 lines are the file header
                    continue
                elif line.startswith('BEGIN:VEVENT'):
                    event = {}
                elif line.startswith('END:VEVENT'):
                    events.append(event)
                else:
                    parsed_line = line.split(':')
                    if len(parsed_line) > 1:
                        event[parsed_line[0]] = parsed_line[1]
                    else:
                        event['DESCRIPTION'] += line

        location_match = re.findall(r"([A-Za-z0-9&_']+)_\d{8}-\d{8}.ics", file_path)[0]
        location = location_match.replace('_', ' ')
        app.logger.info(f'File contains {len(events)} events in {location}')
        if recording_sched and location == recording_sched.meeting.room.name:
            self.compare_ical_export_to_recording_schedule(events, start_date, end_date, recording_sched)
        else:
            for event in events:
                assert event
                assert event['CLASS'] == 'PUBLIC\n'
                assert event['DESCRIPTION']
                assert event['DTSTART']
                assert event['DTEND']
                assert event['LOCATION'] == f'{get_kaltura_safe_name(location)}\n'
                assert event['STATUS'] == 'CONFIRMED\n'
                assert event['SUMMARY'].startswith('qqq')
                assert event['TRANSP'] == 'OPAQUE\n'
        return events

    def compare_ical_export_to_recording_schedule(self, events, start_date, end_date, recording_sched):
        expected_recording_dates = recording_sched.meeting.meeting_schedule.expected_recording_dates(recording_sched.section.term)
        expected_section_event_dates = [d for d in expected_recording_dates if start_date <= d <= end_date]
        expected_summary = f'qqq {recording_sched.section.ccn}\n'

        section_events = [event for event in events if event['SUMMARY'] == expected_summary]
        app.logger.info(
            f'File contains {len(section_events)} events for section {recording_sched.section.ccn}; expected {len(expected_section_event_dates)}',

        )
        assert len(section_events) == len(expected_section_event_dates)

        if len(expected_recording_dates):
            berkeley_start_time = recording_sched.meeting.meeting_schedule.get_berkeley_start_time()
            berkeley_end_time = recording_sched.meeting.meeting_schedule.get_berkeley_end_time()
            recording_start_time = time(berkeley_start_time.hour, berkeley_start_time.minute)
            recording_end_time = time(berkeley_end_time.hour, berkeley_end_time.minute)
            expected_description = f'{recording_sched.section.code}, {recording_sched.section.number}'
            expected_location = f'{get_kaltura_safe_name(recording_sched.meeting.room.name)}\n'

            section_events = iter(section_events)
            for recording_date in expected_section_event_dates:
                recording_start = datetime.combine(recording_date, recording_start_time).astimezone(default_timezone())
                recording_end = datetime.combine(recording_date, recording_end_time).astimezone(default_timezone())
                expected_start_date = f"{recording_start.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\n"
                expected_end_date = f"{recording_end.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\n"
                event = next(section_events, None)
                assert event
                util.assert_equivalence(event['CLASS'], 'PUBLIC\n')
                assert event['DESCRIPTION'].startswith(expected_description)
                util.assert_equivalence(event['DTSTART'], expected_start_date)
                util.assert_equivalence(event['DTEND'], expected_end_date)
                util.assert_equivalence(event['LOCATION'], expected_location)
                util.assert_equivalence(event['STATUS'], 'CONFIRMED\n')
                util.assert_equivalence(event['TRANSP'], 'OPAQUE\n')
