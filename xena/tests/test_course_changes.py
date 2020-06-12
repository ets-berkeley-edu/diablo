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
from xena.models.async_job import AsyncJob
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseChanges:

    real_test_data = util.parse_course_test_data()[8]
    fake_test_data = util.parse_course_test_data()[9]
    real_section = Section(real_test_data)
    fake_section = Section(fake_test_data)
    recording_sched = RecordingSchedule(real_section)

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_data(self):
        util.reset_sign_up_test_data(self.real_test_data)
        self.recording_sched.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_sched.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_sis_data_refresh_pre_run(self):
        self.jobs_page.run_sis_data_refresh_job()

    def test_admin_emails_pre_run(self):
        self.jobs_page.run_admin_emails_job()

    def test_instructor_emails_pre_run(self):
        self.jobs_page.run_instructor_emails_job()

    def test_queued_emails_pre_run(self):
        self.jobs_page.run_queued_emails_job()

    def test_delete_old_kaltura_series(self):
        self.kaltura_page.log_in_via_calnet()
        self.kaltura_page.reset_test_data(self.term, self.recording_sched)

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    # SCHEDULED COURSE CHANGES INSTRUCTOR

    def test_set_fake_instr(self):
        util.change_course_instructor(self.fake_section, self.real_section.instructors[0], self.fake_section.instructors[0])

    def test_sign_up_with_fake_instr(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.fake_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.fake_section)
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()

    def test_schedule_recordings_with_fake_instr(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.wait_for_kaltura_id(self.recording_sched, self.term)

    def test_run_sis_job_to_revert_to_real_instr(self):
        self.jobs_page.run_sis_data_refresh_job()

    def test_run_admin_email_job_with_instr_change(self):
        self.jobs_page.run_admin_emails_job()

    def test_run_queued_email_job_with_instr_change(self):
        self.jobs_page.run_queued_emails_job()

    def test_changes_page_with_instr_change(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)
        fake_instr_name = f'{self.fake_section.instructors[0].first_name} {self.fake_section.instructors[0].last_name}'
        fake_instr_text = f'{fake_instr_name} ({self.fake_section.instructors[0].uid})'
        real_instr_name = f'{self.real_section.instructors[0].first_name} {self.real_section.instructors[0].last_name}'
        real_instr_text = f'{real_instr_name} ({self.real_section.instructors[0].uid})'
        expected = f'{fake_instr_text}\n changed to\n {real_instr_text}'
        actual = self.changes_page.course_instructor_info(self.real_section)
        assert expected in actual

    # TODO - verify filters

    def test_admin_emails_with_instr_change(self):
        subj = f'Course Capture Admin: {self.real_section.code} Instructor changes'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)

    def test_real_instr_approves(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.real_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.real_section)
        # TODO - verify text and static options
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()

    def test_changes_page_new_instr_approved(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)

    def test_update_recordings_with_new_instr(self):
        self.changes_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_changes_page_new_instr_in_kaltura(self):
        # TODO verify the new instructor has replaced the old in the collaborators
        self.changes_page.load_page()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.real_section)

    # SCHEDULED COURSE CHANGES MEETING TIME

    def test_set_fake_meeting_time(self):
        util.set_course_meeting_time(self.fake_section)

    def test_run_admin_email_job_with_new_times(self):
        self.jobs_page.load_page()
        self.jobs_page.run_admin_emails_job()

    def test_run_queued_email_job_with_new_times(self):
        self.jobs_page.run_queued_emails_job()

    def test_changes_page_with_new_times(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)
        fake_start = datetime.strftime(datetime.strptime(self.fake_section.start_time, '%I:%M%p'), '%I:%M %p')
        fake_end = datetime.strftime(datetime.strptime(self.fake_section.end_time, '%I:%M%p'), '%I:%M %p')
        real_start = datetime.strftime(datetime.strptime(self.real_section.start_time, '%I:%M%p'), '%I:%M %p')
        real_end = datetime.strftime(datetime.strptime(self.real_section.end_time, '%I:%M%p'), '%I:%M %p')
        fake_sched = f'{self.fake_section.days.replace(" ", "")} {fake_start} - {fake_end}'
        real_sched = f'{self.real_section.days.replace(" ", "")} {real_start} - {real_end}'
        expected = f'{real_sched}\n changed to\n{fake_sched}'
        actual = self.changes_page.course_schedule_info(self.real_section)
        assert expected in actual

    # TODO - admin email?

    def test_admin_unsched_new_times(self):
        self.sign_up_page.load_page(self.real_section)
        self.sign_up_page.confirm_unscheduling(self.recording_sched)

    def test_changes_page_unsched(self):
        self.sign_up_page.click_course_changes_link()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.real_section)

    def test_admin_resched_new_times(self):
        self.sign_up_page.load_page(self.real_section)
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_approve_button()

    def test_run_jobs_with_resched(self):
        self.sign_up_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        old_series_id = self.recording_sched.series_id
        self.kaltura_page.load_event_edit_page(old_series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_verify_new_kaltura_series_id(self):
        util.wait_for_kaltura_id(self.recording_sched, self.term)

    def test_verify_new_kaltura_series(self):
        self.sign_up_page.load_page(self.real_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched)
        self.kaltura_page.wait_for_delete_button()
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == expected

    def test_verify_new_kaltura_days(self):
        self.kaltura_page.open_recurrence_modal()
        mon_checked = self.kaltura_page.is_mon_checked()
        tue_checked = self.kaltura_page.is_tue_checked()
        wed_checked = self.kaltura_page.is_wed_checked()
        thu_checked = self.kaltura_page.is_thu_checked()
        fri_checked = self.kaltura_page.is_fri_checked()
        assert mon_checked if 'MO' in self.fake_section.days else not mon_checked
        assert tue_checked if 'TU' in self.fake_section.days else not tue_checked
        assert wed_checked if 'WE' in self.fake_section.days else not wed_checked
        assert thu_checked if 'TH' in self.fake_section.days else not thu_checked
        assert fri_checked if 'FR' in self.fake_section.days else not fri_checked
        assert not self.kaltura_page.is_sat_checked()
        assert not self.kaltura_page.is_sun_checked()

    def test_verify_new_kaltura_times(self):
        start = self.fake_section.get_berkeley_start_time()
        visible_start = datetime.strptime(self.kaltura_page.visible_start_time(), '%I:%M %p')
        assert visible_start == start
        end = self.fake_section.get_berkeley_end_time()
        visible_end = datetime.strptime(self.kaltura_page.visible_end_time(), '%I:%M %p')
        assert visible_end == end

    def test_close_kaltura(self):
        self.kaltura_page.close_window_and_switch()

    # SCHEDULED COURSE MOVES TO INELIGIBLE ROOM

    def test_move_to_ineligible_room(self):
        util.set_course_room(self.fake_section)

    def test_run_admin_email_job_ineligible_room(self):
        self.sign_up_page.click_jobs_link()
        self.jobs_page.run_admin_emails_job()

    def test_run_instr_email_job_ineligible_room(self):
        self.jobs_page.run_instructor_emails_job()

    def test_run_queued_email_job_ineligible_room(self):
        self.jobs_page.run_queued_emails_job()

    def test_changes_page_ineligible_room(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)
        expected = f'{self.real_section.room.name}\n changed to\n{self.fake_section.room.name}'
        actual = self.changes_page.course_room_info(self.real_section)
        assert expected in actual

    def test_admin_unsched_ineligible_room(self):
        self.sign_up_page.load_page(self.real_section)
        # TODO - verify 'ineligible' message on page?
        self.sign_up_page.confirm_unscheduling(self.recording_sched)

    def test_changes_page_ineligible_room_unsched(self):
        self.sign_up_page.click_course_changes_link()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.real_section)

    def test_no_kaltura_series_ineligible_room(self):
        self.kaltura_page.load_event_edit_page(self.recording_sched.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_admin_email_ineligible_room(self):
        subj = f'Course Capture Admin: {self.real_section.code} has moved to {self.fake_section.room.name}'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)

    def test_instructor_email_ineligibel_room(self):
        subj = f'Your course {self.real_section.code} is no longer eligible for Course Capture'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)
