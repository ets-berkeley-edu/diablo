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

from datetime import datetime

import pytest
from xena.models.canvas_site import CanvasSite
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util

"""
SCENARIO:
- Course site is created
- Sole instructor visits sign-up page, selects presentation + presenter, approves
- Recordings scheduled
"""


@pytest.mark.usefixtures('page_objects')
class TestSignUp0:

    test_data = util.parse_course_test_data()[0]
    section = Section(test_data)
    recording_schedule = RecordingSchedule(section)
    site = CanvasSite(
        code=f'XENA SignUp0 - {section.code}',
        name=f'XENA SignUp0 - {section.code}',
        site_id=None,
    )

    # DELETE PRE-EXISTING DATA

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.run_canvas_job()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_kaltura_series(self):
        self.kaltura_page.log_in_via_calnet()
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)

    def test_delete_old_canvas_sites(self):
        self.canvas_page.delete_sites(self.section)

    def test_delete_old_diablo_data(self):
        util.reset_sign_up_test_data(self.test_data)
        self.recording_schedule.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    # TODO - configure email template subjects prior to verifying emails

    # CREATE COURSE SITE

    def test_create_course_site(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site)

    def test_run_canvas_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_canvas_job()

    # TODO - def test_course_site_on_course_page(self):

    # CHECK FILTERS - NOT INVITED

    def test_not_invited_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_not_invited_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_not_invited_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    def test_not_invited_filter_no_email(self):
        self.ouija_page.filter_for_do_not_email()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_not_invited_filter_not_invited(self):
        self.ouija_page.filter_for_not_invited()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_not_invited_filter_invited(self):
        self.ouija_page.filter_for_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_not_invited_filter_partial_approve(self):
        self.ouija_page.filter_for_partially_approved()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_not_invited_filter_queued(self):
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_not_invited_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # RUN JOBS AND VERIFY INVITE

    def test_send_invite_email(self):
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()

    def test_receive_invite_email(self):
        self.recording_schedule.approval_status = RecordingApprovalStatus.INVITED
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    # CHECK FILTERS - INVITED

    def test_invited_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_invited_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_invited_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    def test_invited_filter_no_email(self):
        self.ouija_page.filter_for_do_not_email()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_invited_filter_not_invited(self):
        self.ouija_page.filter_for_not_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_invited_filter_invited(self):
        self.ouija_page.filter_for_invited()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_invited_filter_partial_approve(self):
        self.ouija_page.filter_for_partially_approved()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_invited_filter_queued(self):
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_invited_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # INSTRUCTOR LOGS IN

    def test_home_page(self):
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_diablo_title(f'Your {self.section.term.name} Courses Eligible for Capture')

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

    # VERIFY VARIABLE CONTENT AND EXTERNAL LINKS

    # TODO def test_course_site_on_sign_up(self):

    def test_rec_type_text(self):
        assert self.sign_up_page.is_present(SignUpPage.RECORDING_TYPE_TEXT) is True

    def test_publish_type_text(self):
        assert self.sign_up_page.is_present(SignUpPage.PUBLISH_TYPE_TEXT) is True

    def test_overview_link(self):
        title = 'Course Capture | Educational Technology Services'
        assert self.sign_up_page.external_link_valid(SignUpPage.CC_EXPLAINED_LINK, title) is True

    def test_policies_link(self):
        title = 'Policies | Educational Technology Services'
        assert self.sign_up_page.external_link_valid(SignUpPage.CC_POLICIES_LINK, title) is True

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
        self.recording_schedule.approval_status = RecordingApprovalStatus.APPROVED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.QUEUED_FOR_SCHEDULING

    def test_confirmation(self):
        msg = 'This course is currently queued for scheduling. Recordings will be scheduled in an hour or less. Approved by you.'
        self.sign_up_page.wait_for_approvals_msg(msg)

    # VERIFY OUIJA FILTER

    def test_approved_filter_all(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_queued_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_queued_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    def test_approved_filter_no_email(self):
        self.ouija_page.filter_for_do_not_email()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_approved_filter_not_invited(self):
        self.ouija_page.filter_for_not_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_approved_filter_invited(self):
        self.ouija_page.filter_for_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_approved_filter_partial_approve(self):
        self.ouija_page.filter_for_partially_approved()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_queued_filter_queued(self):
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_approved_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # RUN KALTURA SCHEDULING JOB AND OBTAIN SERIES ID

    def test_kaltura_job(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_schedule_id(self):
        util.wait_for_kaltura_id(self.recording_schedule, self.term)

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.section.room)
        self.rooms_page.click_room_link(self.section.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule) == expected

    def test_room_series_start(self):
        start = util.get_first_recording_date(self.recording_schedule)
        assert self.room_page.series_row_start_date(self.recording_schedule) == start

    def test_room_series_end(self):
        assert self.room_page.series_row_end_date(self.recording_schedule) == self.term.end_date

    def test_room_series_days(self):
        assert self.room_page.series_row_days(self.recording_schedule) == self.section.days.replace(' ', '')

    def test_series_recordings(self):
        self.room_page.expand_series_row(self.recording_schedule)
        expected = util.expected_recording_dates(self.recording_schedule)
        visible = self.room_page.series_recording_start_dates(self.recording_schedule)
        assert visible == expected

    # VERIFY OUIJA FILTER

    def test_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_scheduled_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_scheduled_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    def test_scheduled_filter_no_email(self):
        self.ouija_page.filter_for_do_not_email()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_scheduled_filter_not_invited(self):
        self.ouija_page.filter_for_not_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_scheduled_filter_invited(self):
        self.ouija_page.filter_for_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_scheduled_filter_partial_approve(self):
        self.ouija_page.filter_for_partially_approved()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_scheduled_filter_queued(self):
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is True

    # VERIFY SERIES IN KALTURA

    def test_click_series_link(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == expected

    def test_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == len(self.section.instructors)

    def test_series_collab_rights(self):
        for instr in self.section.instructors:
            assert self.kaltura_page.collaborator_perm(instr) == 'Co-Editor'

    def test_series_publish_status(self):
        assert self.kaltura_page.is_private()

    def test_kaltura_course_site_count(self):
        assert len(self.kaltura_page.publish_category_els) == 1

    def test_kaltura_course_site(self):
        assert self.kaltura_page.is_publish_category_present(self.site)

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

    def test_start_date(self):
        start = util.get_kaltura_term_date_str(util.get_first_recording_date(self.recording_schedule))
        assert self.kaltura_page.visible_start_date() == start

    def test_end_date(self):
        end = util.get_kaltura_term_date_str(self.term.end_date)
        assert self.kaltura_page.visible_end_date() == end

    def test_start_time(self):
        start = self.section.get_berkeley_start_time()
        visible_start = datetime.strptime(self.kaltura_page.visible_start_time(), '%I:%M %p')
        assert visible_start == start

    def test_end_time(self):
        end = self.section.get_berkeley_end_time()
        visible_end = datetime.strptime(self.kaltura_page.visible_end_time(), '%I:%M %p')
        assert visible_end == end

    def test_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # VERIFY EMAIL

    def test_send_schedule_conf_email(self):
        self.jobs_page.load_page()
        self.jobs_page.run_queued_emails_job()

    def test_receive_schedule_conf_email(self):
        subj = f'Your course, {self.section.code}, has been scheduled for Course Capture'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    # VERIFY KALTURA IN COURSE SITE

    # TODO def test_media_in_course_site(self):
