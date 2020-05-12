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

from config import xena
import pytest
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_schedule_status import RecordingScheduleStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.test_utils import util

"""
SCENARIO:
- Instructor 1 signs up
- Instructor 2 signs up, changes recording type
- Recordings scheduled
"""

test_data = util.parse_sign_up_test_data()[2]
util.reset_test_data(test_data)


@pytest.mark.usefixtures('page_objects')
class TestSignUp2:
    section = Section(test_data)
    recording_schedule = RecordingSchedule(section)

    # INSTRUCTOR 1 LOGS IN

    def test_home_page_inst_1(self):
        self.login_page.load_page()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_diablo_title('Home')

    def test_current_term_inst_1(self):
        assert self.ouija_page.visible_heading() == f'Your {xena.CURRENT_TERM_NAME} Courses Eligible for Capture'

    def test_sign_up_link_inst_1(self):
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

    # VERIFY AVAILABLE OPTIONS

    def test_rec_type_options_inst_1(self):
        self.sign_up_page.click_rec_type_input()
        visible_opts = self.sign_up_page.visible_menu_options()
        expected = [RecordingType.SCREENCAST.value['option'], RecordingType.VIDEO.value['option'], RecordingType.SCREENCAST_AND_VIDEO.value['option']]
        assert visible_opts == expected

    def test_publish_options_inst_1(self):
        self.sign_up_page.hit_escape()
        self.sign_up_page.click_publish_type_input()
        visible_opts = self.sign_up_page.visible_menu_options()
        assert visible_opts == [PublishType.BCOURSES.value, PublishType.KALTURA.value]

    # SELECT OPTIONS, APPROVE

    def test_choose_rec_type_inst_1(self):
        self.sign_up_page.select_rec_type(RecordingType.SCREENCAST.value['option'])
        self.recording_schedule.recording_type = RecordingType.SCREENCAST

    def test_choose_publish_type_inst_1(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.recording_schedule.publish_type = PublishType.BCOURSES

    def test_agree_terms_inst_1(self):
        self.sign_up_page.click_agree_checkbox()

    def test_approve_inst_1(self):
        self.sign_up_page.click_approve_button()

    def test_confirmation_inst_1(self):
        self.sign_up_page.wait_for_approval_confirmation()
        self.recording_schedule.status = RecordingScheduleStatus.PARTIALLY_APPROVED

    def test_log_out_inst_1(self):
        self.sign_up_page.log_out()

    # INSTRUCTOR 2 LOGS IN

    def test_home_page_inst_2(self):
        self.login_page.dev_auth(self.section.instructors[1].uid)
        self.ouija_page.wait_for_diablo_title('Home')

    def test_current_term_inst_2(self):
        assert self.ouija_page.visible_heading() == f'Your {xena.CURRENT_TERM_NAME} Courses Eligible for Capture'

    def test_sign_up_link_inst_2(self):
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_inst_1_approved(self):
        assert self.sign_up_page.instructor_approval_present(self.section.instructors[0]) is True

    # VERIFY AVAILABLE OPTIONS

    def test_rec_type_options_inst_2(self):
        self.sign_up_page.click_rec_type_input()
        visible_opts = self.sign_up_page.visible_menu_options()
        expected = [RecordingType.SCREENCAST.value['option'], RecordingType.VIDEO.value['option'], RecordingType.SCREENCAST_AND_VIDEO.value['option']]
        assert visible_opts == expected

    def test_publish_options_inst_2(self):
        self.sign_up_page.hit_escape()
        self.sign_up_page.click_publish_type_input()
        visible_opts = self.sign_up_page.visible_menu_options()
        assert visible_opts == [PublishType.BCOURSES.value, PublishType.KALTURA.value]

    # CHANGE OPTIONS, APPROVE

    def test_choose_rec_type_inst_2(self):
        self.sign_up_page.select_rec_type(RecordingType.VIDEO.value['option'])
        self.recording_schedule.recording_type = RecordingType.VIDEO

    def test_choose_publish_type_inst_2(self):
        self.sign_up_page.select_publish_type(PublishType.KALTURA.value)
        self.recording_schedule.publish_type = PublishType.KALTURA

    def test_agree_terms_inst_2(self):
        self.sign_up_page.click_agree_checkbox()

    def test_approve_inst_2(self):
        self.sign_up_page.click_approve_button()

    def test_confirmation_inst_2(self):
        self.sign_up_page.wait_for_approval_confirmation()
        self.recording_schedule.status = RecordingScheduleStatus.APPROVED

    # TODO VERIFY THE APPROVAL IN DB
    # TODO RUN SCHEDULING JOB
    # TODO VERIFY KALTURA RECORDINGS

    # INSTRUCTOR 1 VIEWS APPROVED SIGN UP

    def test_view_approved_inst_1(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')
        assert self.sign_up_page.instructor_approval_present(self.section.instructors[1]) is True
