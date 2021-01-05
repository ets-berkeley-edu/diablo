"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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

from flask import current_app as app
import pytest
from xena.models.canvas_site import CanvasSite
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util

"""
SCENARIO:
- Course has single meeting
- Instructor 1 signs up
- Course site created
- Instructor 2 signs up, changes recording type
- Recordings scheduled
- Another course site created and attached to series, then original site deleted
"""


@pytest.mark.usefixtures('page_objects')
class TestSignUp2:

    test_data = util.get_test_script_course('test_sign_up_2')
    section = util.get_test_section(test_data)
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section)
    site_1 = CanvasSite(
        code=f'XENA SignUp2A - {section.code}',
        name=f'XENA SignUp2A - {section.code}',
        site_id=None,
    )
    site_2 = CanvasSite(
        code=f'XENA SignUp2B - {section.code}',
        name=f'XENA SignUp2B - {section.code}',
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

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet()
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)
        util.reset_sign_up_test_data(self.section)
        self.recording_schedule.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_run_initial_canvas_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_canvas_job()

    def test_delete_old_canvas_sites(self):
        site_ids = self.canvas_page.delete_section_sites(self.section)
        if any(site_ids):
            self.jobs_page.load_page()
            self.jobs_page.run_canvas_job()

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

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

    def test_not_invited_filter_weird(self):
        self.ouija_page.filter_for_scheduled_weird()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # RUN JOBS AND VERIFY INVITE

    def test_send_invite_email(self):
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()

    def test_receive_invite_email_1(self):
        self.recording_schedule.approval_status = RecordingApprovalStatus.INVITED
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    def test_receive_invite_email_2(self):
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[1].email})'
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

    def test_invited_filter_weird(self):
        self.ouija_page.filter_for_scheduled_weird()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # INSTRUCTOR 1 LOGS IN

    def test_home_page_inst_1(self):
        self.jobs_page.load_page()
        self.jobs_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.term.name} Course')

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
        term_dates = f'{SignUpPage.expected_term_date_str(self.meeting.record_start, self.meeting.record_end)}'
        assert term_dates in self.sign_up_page.visible_meeting_days()[0]

    def test_visible_meeting_time(self):
        assert self.sign_up_page.visible_meeting_time()[0] == f'{self.meeting.start_time} - {self.meeting.end_time}'

    def test_visible_room(self):
        assert self.sign_up_page.visible_rooms()[0] == self.meeting.room.name

    def test_visible_listings(self):
        listing_codes = [li.code for li in self.section.listings]
        assert self.sign_up_page.visible_cross_listing_codes() == listing_codes

    def test_no_visible_site_ids(self):
        assert len(self.sign_up_page.visible_course_site_ids()) == 0

    # VERIFY AVAILABLE OPTIONS

    def test_rec_type_text(self):
        assert self.sign_up_page.is_present(SignUpPage.RECORDING_TYPE_TEXT) is True

    def test_publish_type_text(self):
        assert self.sign_up_page.is_present(SignUpPage.PUBLISH_TYPE_TEXT) is True

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

    def test_pre_approval_msg(self):
        name = f'{self.section.instructors[1].first_name} {self.section.instructors[1].last_name}'
        msg = f'Recordings will be scheduled when we have approvals from you and {name}.'
        self.sign_up_page.wait_for_approvals_msg(msg)

    def test_choose_rec_type_inst_1(self):
        self.sign_up_page.select_rec_type(RecordingType.SCREENCAST.value['option'])
        self.recording_schedule.recording_type = RecordingType.SCREENCAST

    def test_choose_publish_type_inst_1(self):
        self.sign_up_page.select_publish_type(PublishType.KALTURA.value)
        self.recording_schedule.publish_type = PublishType.KALTURA

    def test_agree_terms_inst_1(self):
        self.sign_up_page.click_agree_checkbox()

    def test_approve_inst_1(self):
        self.sign_up_page.click_approve_button()
        self.recording_schedule.approval_status = RecordingApprovalStatus.PARTIALLY_APPROVED

    def test_confirmation_inst_1(self):
        name = f'{self.section.instructors[1].first_name} {self.section.instructors[1].last_name}'
        msg = f'Approved by you. Recordings will be scheduled when we have approval from {name}.'
        self.sign_up_page.wait_for_approvals_msg(msg)

    def test_log_out_inst_1(self):
        self.sign_up_page.log_out()

    # VERIFY OUIJA FILTER

    def test_part_approved_filter_all(self):
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

    def test_part_approved_filter_no_email(self):
        self.ouija_page.filter_for_do_not_email()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_part_approved_filter_not_invited(self):
        self.ouija_page.filter_for_not_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_part_approved_filter_invited(self):
        self.ouija_page.filter_for_invited()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_part_approved_filter_partial_approve(self):
        self.ouija_page.filter_for_partially_approved()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_part_approved_filter_queued(self):
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_part_approved_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_part_approved_filter_weird(self):
        self.ouija_page.filter_for_scheduled_weird()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # VERIFY 'WAITING FOR APPROVAL' EMAIL IS SENT TO INSTRUCTOR 1 ONLY

    def test_send_awaiting_approval_email(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_queued_emails_job()

    def test_receive_awaiting_approval_email_inst_1(self):
        subj = f'Course Capture: {self.section.code} waiting on approval (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    def test_no_receive_awaiting_approval_email_inst_2(self):
        subj = f'Course Capture: {self.section.code} waiting on approval (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    # CREATE COURSE SITE

    def test_create_course_site_one(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site_1)

    def test_enable_media_gallery(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MEDIA_GALLERY_TOOL']):
            self.canvas_page.load_site(self.site_1.site_id)
            self.canvas_page.enable_media_gallery(self.site_1)
            self.canvas_page.click_media_gallery_tool()
        else:
            app.logger.info('Media Gallery is not properly configured')
            raise

    def test_enable_my_media(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MY_MEDIA_TOOL']):
            self.canvas_page.load_site(self.site_1.site_id)
            self.canvas_page.enable_my_media(self.site_1)
            self.canvas_page.click_my_media_tool()
        else:
            app.logger.info('My Media is not properly configured')
            raise

    def test_run_canvas_job_one(self):
        self.jobs_page.load_page()
        self.jobs_page.run_canvas_job()

    # INSTRUCTOR 2 LOGS IN

    def test_home_page_inst_2(self):
        self.jobs_page.load_page()
        self.jobs_page.log_out()
        self.login_page.dev_auth(self.section.instructors[1].uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.term.name} Course')

    def test_sign_up_link_inst_2(self):
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_partial_approval_msg(self):
        name = f'{self.section.instructors[0].first_name} {self.section.instructors[0].last_name}'
        msg = f'Approved by {name}. Recordings will be scheduled when we have approval from you.'
        self.sign_up_page.wait_for_approvals_msg(msg)

    def test_visible_site_ids(self):
        self.sign_up_page.load_page(self.section)
        assert self.sign_up_page.visible_course_site_ids() == [site.site_id for site in self.section.sites]

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
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.recording_schedule.publish_type = PublishType.BCOURSES

    def test_agree_terms_inst_2(self):
        self.sign_up_page.click_agree_checkbox()

    def test_approve_inst_2(self):
        self.sign_up_page.click_approve_button()
        self.recording_schedule.approval_status = RecordingApprovalStatus.APPROVED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.QUEUED_FOR_SCHEDULING

    def test_confirmation_inst_2(self):
        name = f'{self.section.instructors[0].first_name} {self.section.instructors[0].last_name}'
        msg = f'This course is currently queued for scheduling. Recordings will be scheduled in an hour or less. Approved by {name} and you.'
        self.sign_up_page.wait_for_approvals_msg(msg)

    # VERIFY OUIJA FILTER

    def test_approved_filter_all(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_approved_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_approved_sched_status(self):
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

    def test_approved_filter_queued(self):
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_approved_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_approved_filter_weird(self):
        self.ouija_page.filter_for_scheduled_weird()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # VERIFY 'NOTIFY INSTRUCTOR OF CHANGES' EMAIL IS SENT TO INSTRUCTOR 1 ONLY

    def test_send_notify_of_changes_email(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_queued_emails_job()

    def test_receive_notify_of_changes_email_inst_1(self):
        subj = f'Changes to your Course Capture settings for {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        self.email_page.is_message_delivered(expected_message)

    def test_no_receive_notify_of_changes_email_inst_2(self):
        subj = f'Changes to your Course Capture settings for {self.section.code} (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    # RUN KALTURA SCHEDULING JOB AND OBTAIN SERIES ID

    def test_run_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_schedule_success(self):
        util.get_kaltura_id(self.recording_schedule, self.term)

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule) == expected

    def test_room_series_start(self):
        start = self.meeting.expected_recording_dates(self.section.term)[0]
        assert self.room_page.series_row_start_date(self.recording_schedule) == start

    def test_room_series_end(self):
        last_date = self.meeting.expected_recording_dates(self.section.term)[-1]
        assert self.room_page.series_row_end_date(self.recording_schedule) == last_date

    def test_room_series_days(self):
        assert self.room_page.series_row_days(self.recording_schedule) == self.meeting.days.replace(' ', '')

    def test_series_recordings(self):
        self.room_page.expand_series_row(self.recording_schedule)
        expected = self.meeting.expected_recording_dates(self.section.term)
        visible = self.room_page.series_recording_start_dates(self.recording_schedule)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        expected.reverse()
        assert visible == expected

    def test_series_blackouts(self):
        expected = self.meeting.expected_blackout_dates(self.section.term)
        visible = self.room_page.series_recording_blackout_dates(self.recording_schedule)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        expected.reverse()
        assert visible == expected

    def test_open_printable(self):
        self.room_printable_page.open_printable_schedule()

    def test_printable_course(self):
        expected = f'{self.section.code}, {self.section.number}'
        assert self.room_printable_page.visible_course(self.section) == expected

    def test_printable_instructors(self):
        expected = [f'{inst.first_name} {inst.last_name} ({inst.uid})' for inst in self.section.instructors]
        list.sort(expected)
        visible = self.room_printable_page.visible_instructors(self.section)
        list.sort(visible)
        assert visible == expected

    def test_printable_days(self):
        expected = [f'{self.meeting.days}']
        assert self.room_printable_page.visible_days(self.section) == expected

    def test_printable_times(self):
        dates = f'{self.section.term.start_date.strftime("%b %-d, %Y")} - {self.section.term.end_date.strftime("%b %-d, %Y")}'
        times = f'{self.meeting.start_time} - {self.meeting.end_time}'
        assert self.room_printable_page.visible_times(self.section) == [f'{dates}\n{times}']

    def test_printable_rec_type(self):
        expected = self.recording_schedule.recording_type.value['selection']
        assert self.room_printable_page.visible_recording_type(self.section) == expected

    def test_close_printable(self):
        self.room_printable_page.close_printable_schedule()

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

    def test_scheduled_filter_weird(self):
        self.ouija_page.filter_for_scheduled_weird()
        assert self.ouija_page.is_course_in_results(self.section) is False

    # VERIFY SERIES IN KALTURA

    def test_click_series_link(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == expected

    def test_series_desc(self):
        course = f'{self.section.code}, {self.section.number} ({self.term.name})'
        instr_1 = f'{self.section.instructors[0].first_name} {self.section.instructors[0].last_name}'
        instr_2 = f'{self.section.instructors[1].first_name} {self.section.instructors[1].last_name}'
        copy = f"Copyright ©{datetime.strftime(datetime.now(), '%Y')} UC Regents; all rights reserved."
        expected = f'{course} is taught by {instr_1} and {instr_2}. {copy}'
        assert self.kaltura_page.visible_series_desc() == expected

    def test_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == len(self.section.instructors)

    def test_series_collab_rights(self):
        for instr in self.section.instructors:
            assert self.kaltura_page.collaborator_perm(instr) == 'Co-Editor, Co-Publisher'

    def test_recur_weekly(self):
        self.kaltura_page.open_recurrence_modal()
        assert self.kaltura_page.is_weekly_checked()

    def test_recur_frequency(self):
        assert self.kaltura_page.visible_weekly_frequency() == '1'

    def test_recur_monday(self):
        checked = self.kaltura_page.is_mon_checked()
        assert checked if 'MO' in self.meeting.days else not checked

    def test_recur_tuesday(self):
        checked = self.kaltura_page.is_tue_checked()
        assert checked if 'TU' in self.meeting.days else not checked

    def test_recur_wednesday(self):
        checked = self.kaltura_page.is_wed_checked()
        assert checked if 'WE' in self.meeting.days else not checked

    def test_recur_thursday(self):
        checked = self.kaltura_page.is_thu_checked()
        assert checked if 'TH' in self.meeting.days else not checked

    def test_recur_friday(self):
        checked = self.kaltura_page.is_fri_checked()
        assert checked if 'FR' in self.meeting.days else not checked

    def test_recur_saturday(self):
        assert not self.kaltura_page.is_sat_checked()

    def test_recur_sunday(self):
        assert not self.kaltura_page.is_sun_checked()

    def test_start_date(self):
        start = util.get_kaltura_term_date_str(self.meeting.expected_recording_dates(self.section.term)[0])
        assert self.kaltura_page.visible_start_date() == start

    def test_end_date(self):
        end = util.get_kaltura_term_date_str(self.meeting.expected_recording_dates(self.section.term)[-1])
        assert self.kaltura_page.visible_end_date() == end

    def test_start_time(self):
        start = self.meeting.get_berkeley_start_time()
        visible_start = datetime.strptime(self.kaltura_page.visible_start_time(), '%I:%M %p')
        assert visible_start == start

    def test_end_time(self):
        end = self.meeting.get_berkeley_end_time()
        visible_end = datetime.strptime(self.kaltura_page.visible_end_time(), '%I:%M %p')
        assert visible_end == end

    def test_series_publish_status(self):
        self.kaltura_page.reload_page()
        self.kaltura_page.wait_for_publish_category_el()
        assert self.kaltura_page.is_published()

    def test_kaltura_course_site_count_one(self):
        assert len(self.kaltura_page.publish_category_els()) == 1

    def test_kaltura_course_site_one(self):
        assert self.kaltura_page.is_publish_category_present(self.site_1)

    def test_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # VERIFY EMAIL

    def test_send_schedule_conf_email(self):
        self.jobs_page.load_page()
        self.jobs_page.run_queued_emails_job()

    def test_receive_schedule_conf_email_inst_1(self):
        subj = f'Your course, {self.section.code}, has been scheduled for Course Capture (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    def test_receive_schedule_conf_email_inst_2(self):
        subj = f'Your course, {self.section.code}, has been scheduled for Course Capture (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    # INSTRUCTOR 1 VIEWS APPROVED SIGN UP

    def test_view_approved_inst_1(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')
        name = f'{self.section.instructors[1].first_name} {self.section.instructors[1].last_name}'
        self.sign_up_page.wait_for_approvals_msg(f'Approved by you and {name}.')

    def test_view_scheduled_inst_1(self):
        assert self.sign_up_page.element(SignUpPage.H4_HEADING).text == 'Recordings scheduled'

    # CREATE CANVAS SITE TWO

    def test_create_course_site_two(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site_2)

    def test_enable_media_gallery_2(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MEDIA_GALLERY_TOOL']):
            self.canvas_page.load_site(self.site_2.site_id)
            self.canvas_page.enable_media_gallery(self.site_2)
            self.canvas_page.click_media_gallery_tool()
        else:
            app.logger.info('Media Gallery is not properly configured')
            raise

    def test_enable_my_media_2(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MY_MEDIA_TOOL']):
            self.canvas_page.load_site(self.site_2.site_id)
            self.canvas_page.enable_my_media(self.site_2)
            self.canvas_page.click_my_media_tool()
        else:
            app.logger.info('My Media is not properly configured')
            raise

    def test_run_canvas_job_site_two(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_canvas_job()
        self.jobs_page.run_kaltura_job()

    def test_two_visible_site_ids(self):
        self.sign_up_page.load_page(self.section)
        assert self.sign_up_page.visible_course_site_ids() == [site.site_id for site in self.section.sites]

    # VERIFY SITES IN KALTURA SERIES

    def test_load_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()

    def test_kaltura_published_status(self):
        self.kaltura_page.wait_for_publish_category_el()
        assert self.kaltura_page.is_published()

    def test_kaltura_course_site_count_two(self):
        assert len(self.kaltura_page.publish_category_els()) == 2

    def test_kaltura_course_site_both(self):
        assert self.kaltura_page.is_publish_category_present(self.site_1)
        assert self.kaltura_page.is_publish_category_present(self.site_2)

    # DELETE COURSE SITE 1

    def test_delete_course_site(self):
        self.canvas_page.delete_site(self.site_1.site_id)
        self.section.sites.remove(self.site_1)

    def test_run_jobs(self):
        self.jobs_page.load_page()
        self.jobs_page.run_canvas_job()
        self.jobs_page.run_kaltura_job()

    def test_one_visible_site_id(self):
        self.sign_up_page.load_page(self.section)
        assert self.sign_up_page.visible_course_site_ids() == [site.site_id for site in self.section.sites]

    # VERIFY SITES IN KALTURA SERIES

    def test_load_kaltura_series_again(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()

    def test_kaltura_course_site_count_still_two(self):
        self.kaltura_page.wait_for_publish_category_el()
        assert len(self.kaltura_page.publish_category_els()) == 2

    def test_kaltura_course_site_still_both(self):
        assert self.kaltura_page.is_publish_category_present(self.site_1)
        assert self.kaltura_page.is_publish_category_present(self.site_2)
