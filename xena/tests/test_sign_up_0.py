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

import pytest
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_schedule_status import RecordingScheduleStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util

"""
SCENARIO:
- Sole instructor visits sign-up page, selects presentation + presenter, approves
- Recordings scheduled
"""


@pytest.mark.usefixtures('page_objects')
class TestSignUp0:

    test_data = util.parse_sign_up_test_data()[0]
    section = Section(test_data)
    recording_schedule = RecordingSchedule(section)

    # DELETE PRE-EXISTING DATA

    def test_delete_old_kaltura_series(self):
        self.kaltura_page.log_in()
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)

    def test_delete_old_diablo_data(self):
        util.reset_test_data(self.test_data)

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    # TODO - configure email template subjects prior to verifying emails

    # INSTRUCTOR LOGS IN

    def test_home_page(self):
        self.login_page.load_page()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_diablo_title('Home')

    def test_current_term(self):
        assert self.ouija_page.visible_heading() == f'Your {self.term.name} Courses Eligible for Capture'

    def test_sign_up_link(self):
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    # VERIFY STATIC COURSE SIS DATA

    def test_visible_ccn(self):
        assert self.sign_up_page.visible_ccn() == self.section.ccn

    def test_visible_course_title(self):
        assert self.sign_up_page.visible_course_title() == self.section.title

    def test_visible_instructors(self):
        instructor_names = [f'{i.first_name} {i.last_name}' for i in self.section.instructors]
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_visible_meeting_days(self):
        assert self.sign_up_page.visible_meeting_days() == self.section.days

    def test_visible_meeting_time(self):
        assert self.sign_up_page.visible_meeting_time() == f'{self.section.start_time} - {self.section.end_time}'

    def test_visible_room(self):
        assert self.sign_up_page.visible_rooms() == self.section.room.name

    def test_visible_listings(self):
        listing_codes = [li.code for li in self.section.listings]
        assert self.sign_up_page.visible_cross_listing_codes() == listing_codes

    # VERIFY TOOLTIPS AND EXTERNAL LINKS

    def test_rec_type_tooltip(self):
        self.sign_up_page.open_rec_type_tooltip()
        # TODO verify tooltip content

    def test_publish_tooltip(self):
        self.sign_up_page.open_publish_tooltip()
        # TODO verify tooltip content

    def test_overview_link(self):
        assert self.sign_up_page.external_link_valid(SignUpPage.CC_EXPLAINED_LINK, 'Course Capture | Educational Technology Services') is True

    def test_policies_link(self):
        assert self.sign_up_page.external_link_valid(SignUpPage.CC_POLICIES_LINK, 'Policies | Educational Technology Services') is True

    # VERIFY AVAILABLE OPTIONS AND DISABLED APPROVE BUTTON

    def test_rec_type_options(self):
        self.sign_up_page.click_rec_type_input()
        visible_opts = self.sign_up_page.visible_menu_options()
        expected = [RecordingType.SCREENCAST.value['option'], RecordingType.VIDEO.value['option'], RecordingType.SCREENCAST_AND_VIDEO.value['option']]
        assert visible_opts == expected

    def test_publish_options(self):
        self.sign_up_page.hit_escape()
        self.sign_up_page.click_publish_type_input()
        visible_opts = self.sign_up_page.visible_menu_options()
        assert visible_opts == [PublishType.BCOURSES.value, PublishType.KALTURA.value]

    def test_approve_disabled_no_selections(self):
        self.sign_up_page.hit_escape()
        assert self.sign_up_page.element(SignUpPage.APPROVE_BUTTON).get_attribute('disabled') == 'true'

    # SELECT OPTIONS, APPROVE

    def test_choose_rec_type(self):
        self.sign_up_page.select_rec_type(RecordingType.SCREENCAST_AND_VIDEO.value['option'])
        self.recording_schedule.recording_type = RecordingType.SCREENCAST_AND_VIDEO

    def test_approve_disabled_no_pub_no_terms(self):
        assert self.sign_up_page.element(SignUpPage.APPROVE_BUTTON).get_attribute('disabled') == 'true'

    def test_choose_publish_type(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.recording_schedule.publish_type = PublishType.BCOURSES

    def test_approve_disabled_no_terms(self):
        assert self.sign_up_page.element(SignUpPage.APPROVE_BUTTON).get_attribute('disabled') == 'true'

    def test_agree_terms(self):
        self.sign_up_page.click_agree_checkbox()

    def test_approve(self):
        self.sign_up_page.click_approve_button()

    def test_confirmation(self):
        self.sign_up_page.wait_for_approval_confirmation()
        self.recording_schedule.status = RecordingScheduleStatus.APPROVED

    # RUN KALTURA SCHEDULING JOB AND OBTAIN SERIES ID

    def test_kaltura_job(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_schedule_id(self):
        util.wait_for_kaltura_id(self.recording_schedule, self.term)

    # VERIFY SERIES IN KALTURA

    def test_load_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule)

    def test_series_title(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == expected

    def test_start_date(self):
        start = util.get_kaltura_term_date_str(self.term.start_date)
        assert f'effective {start}' in self.kaltura_page.visible_recurrence_desc()

    def test_end_date(self):
        end = util.get_kaltura_term_date_str(self.term.end_date)
        assert f'until {end}' in self.kaltura_page.visible_recurrence_desc()

    def test_recur_weekly(self):
        self.kaltura_page.open_recurrence_modal()
        assert self.kaltura_page.is_weekly_checked()

    def test_recur_frequency(self):
        assert self.kaltura_page.visible_weekly_frequency() == '1'

    def test_recur_monday(self):
        checked = self.kaltura_page.is_mon_checked()
        assert checked if 'MO' in self.section.days else not checked

    def test_recur_tuesday(self):
        checked = self.kaltura_page.is_tue_checked()
        assert checked if 'TU' in self.section.days else not checked

    def test_recur_wednesday(self):
        checked = self.kaltura_page.is_wed_checked()
        assert checked if 'WE' in self.section.days else not checked

    def test_recur_thursday(self):
        checked = self.kaltura_page.is_thu_checked()
        assert checked if 'TH' in self.section.days else not checked

    def test_recur_friday(self):
        checked = self.kaltura_page.is_fri_checked()
        assert checked if 'FR' in self.section.days else not checked

    def test_recur_saturday(self):
        assert not self.kaltura_page.is_sat_checked()

    def test_recur_sunday(self):
        assert not self.kaltura_page.is_sun_checked()

    def test_start_time(self):
        start = self.section.get_berkeley_start_time_str()
        assert self.kaltura_page.visible_start_time() == start

    def test_end_time(self):
        end = self.section.get_berkeley_end_time_str()
        assert self.kaltura_page.visible_end_time() == end

    # VERIFY EMAIL

    def test_schedule_conf_email(self):
        subj = f'Your course, {self.section.code}, has been scheduled for Course Capture'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)
