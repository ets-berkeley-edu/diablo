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

from datetime import datetime
from datetime import timedelta

from flask import current_app as app
import pytest
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.pages.course_changes_page import CourseChangesPage
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util

"""
SCENARIO:
- Course has two meetings in sequential date patterns, one of which is eligible
- Course site is created
- Sole instructor visits sign-up page, approves eligible one
- Series is scheduled for right dates
- Instructor, room, and dates change for the scheduled meeting; room changes for the unscheduled meeting
"""


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeC:

    # Initial course data
    test_data = util.get_test_script_course('test_weird_type_c')
    section = util.get_test_section(test_data)
    meeting_0 = section.meetings[0]
    meeting_1 = section.meetings[1]
    instructor_0 = section.instructors[0]
    recording_schedule = RecordingSchedule(section)

    end_0 = (meeting_0.start_date + timedelta(days=14)).strftime('%Y-%m-%d')
    meeting_0.end_date = end_0
    start_1 = (meeting_0.start_date + timedelta(days=15)).strftime('%Y-%m-%d')
    meeting_1.start_date = start_1

    # Course changes data
    test_data_changes = util.get_test_script_course('test_weird_type_c_changes')
    section_changes = Section(test_data_changes)
    meeting_0_changes = section_changes.meetings[0]
    meeting_1_changes = section_changes.meetings[1]
    instructor_1 = section_changes.instructors[0]
    recording_schedule_changes = RecordingSchedule(section_changes)

    end_0 = (meeting_0.end_date + timedelta(days=7)).strftime('%Y-%m-%d')
    meeting_0_changes.end_date = end_0
    start_1 = (meeting_1.start_date + timedelta(days=7)).strftime('%Y-%m-%d')
    meeting_1_changes.start_date = start_1

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_admin_emails_pre_run(self):
        self.jobs_page.run_admin_emails_job()

    def test_instructor_emails_pre_run(self):
        self.jobs_page.run_instructor_emails_job()

    def test_queued_emails_pre_run(self):
        self.jobs_page.run_queued_emails_job()

    def test_create_blackouts(self):
        self.jobs_page.click_blackouts_link()
        self.blackouts_page.delete_all_blackouts()
        self.blackouts_page.create_all_blackouts()

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet()
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)
        util.reset_sign_up_test_data(self.section)
        self.recording_schedule.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    # COURSE APPEARS ON 'NOT INVITED' FILTER

    def test_not_invited_filter_not_invited(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_not_invited_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_not_invited_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    # RUN JOBS AND VERIFY INVITE

    def test_send_invite_email(self):
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()
        self.recording_schedule.approval_status = RecordingApprovalStatus.INVITED

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_receive_invite_email(self):
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    # COURSE APPEARS ON 'INVITED' FILTER

    def test_invited_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_invited()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_invited_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_invited_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    # INSTRUCTOR LOGS IN

    def test_home_page(self):
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_0.uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')

    def test_sign_up_link(self):
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    # VERIFY STATIC COURSE SIS DATA

    def test_visible_ccn(self):
        assert self.sign_up_page.visible_ccn() == self.section.ccn

    def test_visible_course_title(self):
        assert self.sign_up_page.visible_course_title() == self.section.title

    def test_visible_instructors(self):
        instructor_names = [f'{self.instructor_0.first_name} {self.instructor_0.last_name}']
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_visible_meeting_days(self):
        term_dates = f'{SignUpPage.expected_term_date_str(self.meeting_0.record_start, self.section.term.end_date)}'
        assert term_dates in self.sign_up_page.visible_meeting_days()[0]
        assert len(self.sign_up_page.visible_meeting_days()) == 1

    def test_visible_meeting_time(self):
        assert self.sign_up_page.visible_meeting_time()[0] == f'{self.meeting_0.start_time} - {self.meeting_0.end_time}'
        assert len(self.sign_up_page.visible_meeting_time()) == 1

    def test_visible_room(self):
        assert self.sign_up_page.visible_rooms()[0] == self.meeting_0.room.name
        assert len(self.sign_up_page.visible_rooms()) == 1

    # SELECT OPTIONS, APPROVE

    def test_set_rec_type(self):
        self.sign_up_page.select_rec_type(RecordingType.SCREENCAST.value['option'])
        self.recording_schedule.recording_type = RecordingType.SCREENCAST

    def test_choose_publish_type(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.recording_schedule.publish_type = PublishType.BCOURSES

    def test_agree_terms(self):
        self.sign_up_page.click_agree_checkbox()

    def test_approve(self):
        self.sign_up_page.click_approve_button()
        self.recording_schedule.approval_status = RecordingApprovalStatus.APPROVED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.QUEUED_FOR_SCHEDULING

    def test_confirmation(self):
        msg = 'This course is currently queued for scheduling.'
        self.sign_up_page.wait_for_approvals_msg(msg)

    # COURSE APPEARS ON 'QUEUED' FILTER

    def test_approved_filter_all(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_queued_for_scheduling()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_queued_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_queued_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    # RUN KALTURA SCHEDULING JOB AND OBTAIN SERIES ID

    def test_kaltura_job(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_schedule_id(self):
        util.get_kaltura_id(self.recording_schedule, self.term)

    def test_kaltura_blackouts(self):
        self.jobs_page.run_blackouts_job()

    def test_run_admin_emails_post_scheduling(self):
        self.jobs_page.run_admin_emails_job()
        self.jobs_page.run_queued_emails_job()

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_0.room)
        self.rooms_page.click_room_link(self.meeting_0.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule) == expected

    def test_room_series_start(self):
        start = self.meeting_0.expected_recording_dates(self.section.term)[0]
        assert self.room_page.series_row_start_date(self.recording_schedule) == start

    def test_room_series_end(self):
        last_date = self.meeting_0.expected_recording_dates(self.section.term)[-1]
        assert self.room_page.series_row_end_date(self.recording_schedule) == last_date

    def test_room_series_days(self):
        assert self.room_page.series_row_days(self.recording_schedule) == self.meeting_0.days.replace(' ', '')

    def test_series_recordings(self):
        self.room_page.expand_series_row(self.recording_schedule)
        expected = self.meeting_0.expected_recording_dates(self.section.term)
        visible = self.room_page.series_recording_start_dates(self.recording_schedule)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        expected.reverse()
        assert visible == expected

    def test_series_blackouts(self):
        expected = self.meeting_0.expected_blackout_dates(self.section.term)
        visible = self.room_page.series_recording_blackout_dates(self.recording_schedule)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        assert visible == expected

    # COURSE APPEARS ON 'SCHEDULED, NON-STANDARD DATES' FILTER

    def test_scheduled_filter_weird(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_scheduled_weird()
        assert self.ouija_page.is_course_in_results(self.section) is True

    def test_scheduled_approval_status(self):
        visible_status = self.ouija_page.course_row_approval_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.approval_status.value

    def test_scheduled_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule.scheduling_status.value

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is False

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
            assert self.kaltura_page.collaborator_perm(instr) == 'Co-Editor, Co-Publisher'

    def test_recur_weekly(self):
        self.kaltura_page.open_recurrence_modal()
        assert self.kaltura_page.is_weekly_checked()

    def test_recur_frequency(self):
        assert self.kaltura_page.visible_weekly_frequency() == '1'

    def test_recur_monday(self):
        checked = self.kaltura_page.is_mon_checked()
        assert checked if 'MO' in self.meeting_0.days else not checked

    def test_recur_tuesday(self):
        checked = self.kaltura_page.is_tue_checked()
        assert checked if 'TU' in self.meeting_0.days else not checked

    def test_recur_wednesday(self):
        checked = self.kaltura_page.is_wed_checked()
        assert checked if 'WE' in self.meeting_0.days else not checked

    def test_recur_thursday(self):
        checked = self.kaltura_page.is_thu_checked()
        assert checked if 'TH' in self.meeting_0.days else not checked

    def test_recur_friday(self):
        checked = self.kaltura_page.is_fri_checked()
        assert checked if 'FR' in self.meeting_0.days else not checked

    def test_recur_saturday(self):
        assert not self.kaltura_page.is_sat_checked()

    def test_recur_sunday(self):
        assert not self.kaltura_page.is_sun_checked()

    def test_start_date(self):
        start = util.get_kaltura_term_date_str(self.meeting_0.expected_recording_dates(self.section.term)[0])
        assert self.kaltura_page.visible_start_date() == start

    def test_end_date(self):
        end = util.get_kaltura_term_date_str(self.meeting_0.expected_recording_dates(self.section.term)[-1])
        assert self.kaltura_page.visible_end_date() == end

    def test_start_time(self):
        start = self.meeting_0.get_berkeley_start_time()
        visible_start = datetime.strptime(self.kaltura_page.visible_start_time(), '%I:%M %p')
        assert visible_start == start

    def test_end_time(self):
        end = self.meeting_0.get_berkeley_end_time()
        visible_end = datetime.strptime(self.kaltura_page.visible_end_time(), '%I:%M %p')
        assert visible_end == end

    def test_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # VERIFY 'WEIRD' ADMIN EMAIL RECEIVED

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_weird_email(self):
        subj = f'Admin alert: {self.section.code} is weird'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    # INSTRUCTOR REMOVED

    def test_remove_instructor(self):
        util.change_course_instructor(self.section, old_instructor=self.instructor_0, new_instructor=None)

    def test_instr_removed_summary(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_course_row(self.section)
        expected = 'Instructors are obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_instr_removed_former_instr(self):
        expected = f'{self.instructor_0.first_name} {self.instructor_0.last_name} ({self.instructor_0.uid})'
        actual = self.changes_page.scheduled_card_old_instructors(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    # INSTRUCTOR ADDED

    def test_add_instructor(self):
        util.change_course_instructor(self.section, old_instructor=None, new_instructor=self.instructor_1)

    def test_instr_changed_summary(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_course_row(self.section)
        expected = 'Instructors are obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_instr_changed_former_instr(self):
        expected = f'{self.instructor_0.first_name} {self.instructor_0.last_name} ({self.instructor_0.uid})'
        actual = self.changes_page.scheduled_card_old_instructors(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_instr_changed_new_instr(self):
        expected = f'{self.instructor_1.first_name} {self.instructor_1.last_name} ({self.instructor_1.uid})'
        actual = self.changes_page.scheduled_card_new_instructors(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_instr_changed_current_card(self):
        expected = f'{self.instructor_1.first_name} {self.instructor_1.last_name} ({self.instructor_1.uid})'
        actual = self.changes_page.current_card_instructors(self.section, 1)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    # START / END DATES CHANGE FOR ELIGIBLE SECTION

    def test_change_dates(self):
        start = self.meeting_0_changes.start_date
        end = self.meeting_0_changes.end_date
        util.update_course_start_end_dates(self.section, self.meeting_0_changes.room, start, end)

    def test_dates_changed_summary(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_course_row(self.section)
        expected = 'Instructors and dates are obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_dates_changed_former_sched_room(self):
        expected = self.meeting_0.room.name
        actual = self.changes_page.scheduled_card_old_room(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_dates_changed_former_sched_dates(self):
        dates = self.meeting_0.expected_recording_dates(self.section.term)
        start = dates[0]
        end = dates[-1]
        dates = f'{start.strftime("%Y-%m-%d")} to {end.strftime("%Y-%m-%d")}'
        times = CourseChangesPage.meeting_time_str(self.meeting_0)
        days_times = f'{self.meeting_0.days.replace(" ", "").replace(",", "")}, {times}'
        expected = f'{dates}{days_times}'.upper()
        actual = self.changes_page.scheduled_card_old_schedule(self.section).upper()
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_dates_changed_current_room_1(self):
        expected = self.meeting_0.room.name
        actual = self.changes_page.current_card_schedule(self.section, 1, 1)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_dates_changed_current_dates_1(self):
        dates = self.meeting_0_changes.expected_recording_dates(self.section.term)
        start = dates[0]
        end = dates[-1]
        dates = f'{start.strftime("%Y-%m-%d")} to {end.strftime("%Y-%m-%d")}'
        days = self.meeting_0_changes.days.replace(' ', '').replace(',', '')
        times = CourseChangesPage.meeting_time_str(self.meeting_0_changes)
        expected = f'{dates}{days}, {times}'.upper()
        actual = self.changes_page.current_card_schedule(self.section, 1, 2).upper()
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_dates_changed_current_room_2(self):
        expected = self.meeting_1.room.name
        actual = self.changes_page.current_card_schedule(self.section, 2, 1)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_dates_changed_current_dates_2(self):
        start = self.meeting_1.start_date
        end = self.meeting_1.end_date
        dates = f'{start.strftime("%Y-%m-%d")} to {end.strftime("%Y-%m-%d")}'
        days = self.meeting_1.days.replace(' ', '').replace(',', '')
        times = CourseChangesPage.meeting_time_str(self.meeting_1)
        expected = f'{dates}{days}, {times}'.upper()
        actual = self.changes_page.current_card_schedule(self.section, 2, 2).upper()
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    # ROOM REMOVED

    def test_remove_room(self):
        util.change_course_room(self.section, old_room=self.meeting_0.room, new_room=None)

    def test_room_removed_summary(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_course_row(self.section)
        expected = 'Instructors and room are obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_room_removed_former_room(self):
        actual = self.changes_page.scheduled_card_old_room(self.section)
        app.logger.info(f'Expecting: {self.meeting_0.room.name}')
        app.logger.info(f'Actual: {actual}')
        assert self.meeting_0.room.name in actual

    def test_room_removed_current_card(self):
        actual = self.changes_page.current_card_schedule(self.section, list_node=None, detail_node=1)
        app.logger.info(f'Expecting: {self.meeting_1.room.name}')
        app.logger.info(f'Actual: {actual}')
        assert self.meeting_1.room.name in actual

    # ROOM ADDED

    def test_add_room(self):
        util.change_course_room(self.section, old_room=self.meeting_1.room, new_room=self.meeting_1_changes.room)

    def test_room_changed_summary(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_course_row(self.section)
        expected = 'Instructors and room are obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_room_changed_former_room(self):
        actual = self.changes_page.scheduled_card_old_room(self.section)
        app.logger.info(f'Expecting: {self.meeting_0.room.name}')
        app.logger.info(f'Actual: {actual}')
        assert self.meeting_0.room.name in actual

    def test_room_changed_current_card(self):
        actual_1 = self.changes_page.current_card_schedule(self.section, list_node=None, detail_node=1)
        app.logger.info(f'Expecting: {self.meeting_1_changes.room.name}')
        app.logger.info(f'Actual: {actual_1}')
        assert self.meeting_1_changes.room.name in actual_1
