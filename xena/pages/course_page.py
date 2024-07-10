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

import datetime
import time

from flask import current_app as app
from selenium.webdriver.common.by import By
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_type import RecordingType
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class CoursePage(DiabloPages):

    UPDATES_QUEUED_MSG = By.XPATH, '//div[contains(text(), "Recent updates to recording settings are currently queued")]'
    NOT_ELIGIBLE_MSG = (By.ID, 'course-not-eligible')

    @staticmethod
    def instructor_link_locator(instructor):
        return By.ID, f'instructor-{instructor.uid}'

    @staticmethod
    def room_link_locator(room):
        return By.LINK_TEXT, room.name

    @staticmethod
    def not_authorized_msg_locator(section):
        return By.XPATH, f'//span[contains(text(), "Sorry, you are unauthorized to view the course {section.code}, {section.number}")]'

    @staticmethod
    def expected_final_record_date_str(meeting, term):
        return meeting.meeting_schedule.expected_recording_dates(term)[-1].strftime('%b %-d, %Y')

    def hit_url(self, term_id, ccn):
        self.driver.get(f'{app.config["BASE_URL"]}/course/{term_id}/{ccn}')

    def load_page(self, section):
        app.logger.info(f'Loading course page for term {section.term.id} section ID {section.ccn}')
        self.hit_url(section.term.id, section.ccn)
        self.wait_for_diablo_title(f'{section.code}, {section.number}')

    def is_queued_changes_msg_present(self):
        return self.is_present(self.UPDATES_QUEUED_MSG)

    # SIS DATA - section

    SECTION_ID = (By.ID, 'section-id')
    COURSE_TITLE = (By.ID, 'course-title')
    INSTRUCTORS = (By.ID, 'instructors')
    INSTRUCTOR = (By.XPATH, '//div[@id="instructors"]//*[contains(@id, "instructor-") and not(contains(@id, "proxy"))]')
    PROXY = (By.XPATH, '//div[@id="instructors"]//span[contains(@id, "instructor-proxy-")]')
    CROSS_LISTING = (By.XPATH, '//div[contains(@id, "cross-listing-")]')

    def is_canceled(self):
        return self.is_present((By.XPATH, '//span[text()="UC Berkeley has canceled this section."]'))

    def visible_ccn(self):
        return self.element(CoursePage.SECTION_ID).text

    def visible_course_title(self):
        return self.element(CoursePage.COURSE_TITLE).text

    def wait_for_instructors(self):
        self.when_present(self.INSTRUCTOR, util.get_short_timeout())

    def visible_instructors(self):
        els = self.elements(CoursePage.INSTRUCTOR)
        return [el.text for el in els]

    def verify_instructors(self, section):
        expected_instructors = [f'{i.first_name} {i.last_name}'.strip() for i in section.instructors]
        visible_instructors = self.visible_instructors()
        if visible_instructors != expected_instructors:
            app.logger.info(f"Expected '{expected_instructors}', got '{visible_instructors}'")
        assert visible_instructors == expected_instructors

    def verify_section_sis_data(self, section):
        expected_ccn = section.ccn
        visible_ccn = self.visible_ccn()
        if visible_ccn != expected_ccn:
            app.logger.info(f"Expected '{expected_ccn}', got '{visible_ccn}'")

        expected_title = section.title
        visible_title = self.visible_course_title()
        if visible_title != expected_title:
            app.logger.info(f"Expected '{expected_title}', got '{visible_title}'")

        self.verify_instructors(section)
        assert visible_ccn == expected_ccn
        assert visible_title == expected_title

    def visible_proxies(self):
        els = self.elements(CoursePage.PROXY)
        return [el.text for el in els]

    def visible_cross_listing_codes(self):
        return [el.text for el in self.elements(CoursePage.CROSS_LISTING)]

    def visible_cross_listing_ccns(self):
        return [el.get_attribute('id').split('-')[2] for el in self.elements(CoursePage.CROSS_LISTING)]

    # SIS DATA - meeting

    MEETING_DAYS = (By.XPATH, '//div[contains(@id, "meeting-days-")]')
    MEETING_TIMES = (By.XPATH, '//div[contains(@id, "meeting-times-")]')
    ROOMS = (By.XPATH, '//*[contains(@id, "rooms-")]')

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

    def visible_opt_out(self):
        return self.element(CoursePage.OPTED_OUT).get_attribute('innerText').strip()

    def click_room_link(self, room):
        self.wait_for_element_and_click(self.room_link_locator(room))

    def verify_meeting_sis_data(self, meeting, idx):
        expected_room = meeting.room.name
        visible_room = self.visible_rooms()[idx]
        if visible_room != expected_room:
            app.logger.info(f"Expected room '{expected_room}', got '{visible_room}'")

        start_date = meeting.meeting_schedule.start_date.strftime('%b %-d, %Y')
        end_date = meeting.meeting_schedule.end_date.strftime('%b %-d, %Y')
        expected_dates = f'{start_date} to {end_date}'
        visible_dates = self.visible_meeting_days()[idx]
        if expected_dates not in visible_dates:
            app.logger.info(f"Expected '{expected_dates}' to be in '{visible_dates}'")

        expected_times = f'{meeting.meeting_schedule.start_time} - {meeting.meeting_schedule.end_time}'
        visible_times = self.visible_meeting_time()[idx]
        if expected_times not in visible_times:
            app.logger.info(f"Expected '{expected_times}' to be in '{visible_times}'")

        assert visible_room == expected_room
        assert expected_dates in visible_dates
        assert expected_times in visible_times

    # CAPTURE SETTINGS - instructors

    INSTRUCTOR_ROW = By.XPATH, '//div[@id="instructors-list"]/div'

    def visible_instructor_uids(self):
        uids = list(map(lambda el: el.get_attribute('id').split('-')[-1], self.elements(self.INSTRUCTOR_ROW)))
        uids.sort()
        return uids

    # CAPTURE SETTINGS - collaborators

    COLLAB_ROW = By.XPATH, '//div[starts-with(@id, "collaborator-")]'
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
        uids = list(map(lambda el: el.get_attribute('id').split('-')[-1], self.elements(self.COLLAB_ROW)))
        uids.sort()
        return uids

    def verify_collaborator_uids(self, collaborators):
        visible = self.visible_collaborator_uids()
        visible.sort()
        expected = list(map(lambda c: str(c.uid), collaborators))
        expected.sort()
        app.logger.info(f'Expecting collaborator UIDs {expected}, got {visible}')
        assert visible == expected

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

    # CAPTURE SETTINGS - recording type

    RECORDING_TYPE_TEXT = (By.ID, 'recording-type-name')
    RECORDING_TYPE_EDIT_BUTTON = By.ID, 'btn-recording-type-edit'
    RECORDING_TYPE_NO_OP_RADIO = By.ID, 'radio-recording-type-presenter_presentation_audio'
    RECORDING_TYPE_OP_RADIO = By.ID, 'radio-recording-type-presenter_presentation_audio_with_operator'
    RECORDING_TYPE_SAVE_BUTTON = By.ID, 'btn-recording-type-save'
    RECORDING_TYPE_CXL_BUTTON = By.ID, 'btn-recording-type-cancel'

    def visible_recording_type(self):
        return self.element(self.RECORDING_TYPE_TEXT).text.strip()

    def click_rec_type_edit_button(self):
        app.logger.info('Clicking the recording type edit button')
        self.wait_for_element_and_click(CoursePage.RECORDING_TYPE_EDIT_BUTTON)

    def select_rec_type(self, recording_type):
        app.logger.info(f"Selecting recording type {recording_type.value['desc']}")
        if recording_type == RecordingType.VIDEO_WITH_OPERATOR:
            self.wait_for_page_and_click_js(self.RECORDING_TYPE_OP_RADIO)
        else:
            self.wait_for_page_and_click_js(self.RECORDING_TYPE_NO_OP_RADIO)

    def save_recording_type_edits(self):
        self.wait_for_element_and_click(self.RECORDING_TYPE_SAVE_BUTTON)

    def cancel_recording_type_edits(self):
        self.wait_for_page_and_click_js(self.RECORDING_TYPE_CXL_BUTTON)

    def verify_recording_type(self, recording_schedule):
        expected = recording_schedule.recording_type.value['desc']
        visible = self.visible_recording_type()
        if visible != expected:
            app.logger.info(f"Expected recording type '{expected}', got '{visible}'")
        assert visible == expected

    # CAPTURE SETTINGS - recording placement

    PLACEMENT_TEXT = By.ID, 'publish-type-name'
    PLACEMENT_EDIT_BUTTON = By.ID, 'btn-publish-type-edit'
    PLACEMENT_MY_MEDIA_RADIO = By.ID, 'radio-publish-type-kaltura_my_media'
    PLACEMENT_MEDIA_GALLERY_RADIO = By.ID, 'radio-publish-type-kaltura_media_gallery'
    PLACEMENT_SAVE_BUTTON = By.ID, 'btn-publish-type-save'
    PLACEMENT_CXL_BUTTON = By.ID, 'btn-publish-type-cancel'

    PLACEMENT_SITE_SELECT = By.ID, 'select-canvas-site'
    PLACEMENT_SITE_LINK = By.XPATH, '//a[contains(@id, "canvas-course-site-")]'
    PLACEMENT_SITE_ADD_BUTTON = By.ID, 'btn-canvas-site-add'
    PLACEMENT_SITE_INPUT = By.ID, 'input-canvas-site-id'

    @staticmethod
    def placement_site_option_loc(site):
        return By.XPATH, f'//span[@id="menu-option-canvas-site-{site.site_id}"]/..'

    @staticmethod
    def placement_site_remove_button_loc(site):
        return By.ID, f'btn-canvas-site-remove-{site.site_id}'

    @staticmethod
    def selected_placement_site_loc(site):
        return By.ID, f'canvas-course-site-{site.site_id}'

    def visible_course_site_ids(self):
        time.sleep(2)
        site_els = self.elements(self.PLACEMENT_SITE_LINK)
        ids = [el.get_attribute('id').split('-')[-1] for el in site_els]
        ids.sort()
        return ids

    def visible_recording_placement(self):
        return self.element(self.PLACEMENT_TEXT).text.strip()

    def click_edit_recording_placement(self):
        app.logger.info('Clicking the edit recording placement button')
        self.wait_for_element_and_click(self.PLACEMENT_EDIT_BUTTON)

    def select_recording_placement(self, publish_type, sites=None):
        app.logger.info(f'Selecting the radio button for {publish_type}')
        if publish_type == RecordingPlacement.PUBLISH_TO_MY_MEDIA:
            self.wait_for_page_and_click_js(self.PLACEMENT_MY_MEDIA_RADIO)
        elif publish_type == RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY:
            self.wait_for_page_and_click_js(self.PLACEMENT_MEDIA_GALLERY_RADIO)
            if sites:
                for site in sites:
                    self.wait_for_element_and_click(self.PLACEMENT_SITE_SELECT)
                    self.wait_for_element_and_click(self.placement_site_option_loc(site))
                    self.wait_for_element_and_click(self.PLACEMENT_SITE_ADD_BUTTON)

    def enter_recording_placement(self, publish_type, sites=None):
        app.logger.info(f'Selecting the radio button for {publish_type}')
        if publish_type == RecordingPlacement.PUBLISH_TO_MY_MEDIA:
            self.wait_for_page_and_click_js(self.PLACEMENT_MY_MEDIA_RADIO)
        elif publish_type == RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY:
            self.wait_for_page_and_click_js(self.PLACEMENT_MEDIA_GALLERY_RADIO)
            if sites:
                for site in sites:
                    self.wait_for_element_and_type(self.PLACEMENT_SITE_INPUT, str(site.site_id))
                    self.wait_for_element_and_click(self.PLACEMENT_SITE_ADD_BUTTON)

    def remove_recording_placement_site(self, site):
        self.wait_for_page_and_click_js(self.placement_site_remove_button_loc(site))

    def save_recording_placement_edits(self):
        self.wait_for_element_and_click(self.PLACEMENT_SAVE_BUTTON)

    def cancel_recording_placement_edits(self):
        self.wait_for_page_and_click_js(self.PLACEMENT_CXL_BUTTON)

    def verify_recording_placement(self, recording_schedule):
        expected = recording_schedule.recording_placement.value['desc']
        visible = self.visible_recording_placement()
        if expected not in visible:
            app.logger.info(f"Expected '{expected}' to be in '{visible}'")
        assert expected in visible

    # KALTURA SERIES INFO

    @staticmethod
    def kaltura_series_link(recording_schedule):
        return By.PARTIAL_LINK_TEXT, f'Kaltura series {recording_schedule.series_id}'

    def click_kaltura_series_link(self, recording_schedule):
        app.logger.info(f'Clicking the link to Kaltura series ID {recording_schedule.series_id}')
        self.wait_for_page_and_click(CoursePage.kaltura_series_link(recording_schedule))
        time.sleep(2)
        self.switch_to_last_window(self.window_handles())

    # COURSE UPDATE HISTORY

    def update_history_table_rows(self):
        rows = []
        xpath = '//div[@id="update-history-table"]//tbody/tr'
        row_els = self.elements((By.XPATH, xpath))
        for r in row_els:
            node = str(row_els.index(r) + 1)
            old_val = self.visible_value_converter(self.element((By.XPATH, f'{xpath}[{node}]/td[2]')).text)
            new_val = self.visible_value_converter(self.element((By.XPATH, f'{xpath}[{node}]/td[3]')).text)
            rows.append({
                'field': self.element((By.XPATH, f'{xpath}[{node}]/td[1]')).text,
                'old_value': old_val,
                'new_value': new_val,
                'requested_by': self.element((By.XPATH, f'{xpath}[{node}]/td[4]')).text.split('(')[-1][0:-1],
                'requested_at': self.element((By.XPATH, f'{xpath}[{node}]/td[5]')).text.split(',')[0],
                'published_at': self.element((By.XPATH, f'{xpath}[{node}]/td[6]')).text.split(',')[0],
                'status': self.element((By.XPATH, f'{xpath}[{node}]/td[7]')).text,
            })
        return rows

    def verify_history_row(self, field, old_value, new_value, requestor, status, published=False):
        all_visible_rows = self.update_history_table_rows()
        visible_field_rows = [row for row in all_visible_rows if row['field'] == field]
        expected_row = {
            'field': field,
            'old_value': old_value,
            'new_value': new_value,
            'requested_by': (str(requestor.uid) if requestor else ''),
            'requested_at': datetime.date.today().strftime('%-m/%-d/%Y'),
            'published_at': (datetime.date.today().strftime('%-m/%-d/%Y') if published else '—'),
            'status': status,
        }
        app.logger.info(f'Expecting {expected_row}')
        app.logger.info(f'Visible rows of type {field} are {visible_field_rows}')
        assert expected_row in visible_field_rows

    @staticmethod
    def expected_uids_converter(users):
        ary = [str(p.uid) for p in users]
        ary.sort()
        return ary

    @staticmethod
    def expected_site_ids_converter(sites):
        ary = [s.site_id for s in sites]
        ary.sort()
        return ary

    @staticmethod
    def visible_value_converter(val):
        if val[0] == '{':
            return None
        elif val == '[]':
            return []
        elif '[ "' in val:
            val_as_ary = val.replace('[ "', '').replace('" ]', '').split('", "')
            val_as_ary.sort()
            return val_as_ary
        else:
            return val
