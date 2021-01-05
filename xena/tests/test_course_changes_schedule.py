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
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.section import Section
from xena.pages.course_changes_page import CourseChangesPage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseScheduleChanges:
    real_test_data = util.get_test_script_course('test_course_changes_real')
    fake_test_data = util.get_test_script_course('test_course_changes_fake')
    real_section = util.get_test_section(real_test_data)
    real_meeting = real_section.meetings[0]
    fake_section = Section(fake_test_data)
    fake_meeting = fake_section.meetings[0]
    recording_sched = RecordingSchedule(real_section)

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet()
        self.kaltura_page.reset_test_data(self.term, self.recording_sched)
        util.reset_sign_up_test_data(self.real_section)
        self.recording_sched.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_sched.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_admin_emails_pre_run(self):
        self.jobs_page.load_page()
        self.jobs_page.run_admin_emails_job()

    def test_instructor_emails_pre_run(self):
        self.jobs_page.run_instructor_emails_job()

    def test_queued_emails_pre_run(self):
        self.jobs_page.run_queued_emails_job()

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    def test_sign_up(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.real_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.real_section)
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()

    def test_schedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched, self.term)

    def test_run_admin_email_job_post_scheduling(self):
        self.jobs_page.run_admin_emails_job()

    def test_run_queued_email_job_post_scheduling(self):
        self.jobs_page.run_queued_emails_job()

    # SCHEDULED COURSE CHANGES MEETING TIME

    def test_set_fake_meeting_time(self):
        util.set_course_meeting_time(self.real_section, self.fake_section.meetings[0])

    def test_run_admin_email_job_with_new_times(self):
        self.jobs_page.load_page()
        self.jobs_page.run_admin_emails_job()

    def test_run_queued_email_job_with_new_times(self):
        self.jobs_page.run_queued_emails_job()

    def test_changes_page_summary(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)
        expected = 'Times are obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.real_section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_old_room(self):
        expected = self.real_meeting.room.name
        actual = self.changes_page.scheduled_card_old_room(self.real_section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_old_sched(self):
        dates = self.real_meeting.expected_recording_dates(self.real_section.term)
        start = dates[0]
        end = dates[-1]
        dates = f'{start.strftime("%Y-%m-%d")} to {end.strftime("%Y-%m-%d")}'
        days = self.real_meeting.days.replace(' ', '').replace(',', '')
        days_times = f'{days}, {CourseChangesPage.meeting_time_str(self.real_meeting)}'
        expected = f'{dates}{days_times}'.upper()
        actual = self.changes_page.scheduled_card_old_schedule(self.real_section).upper()
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_new_sched(self):
        dates = self.real_meeting.expected_recording_dates(self.real_section.term)
        start = dates[0]
        end = dates[-1]
        dates = f'{start.strftime("%Y-%m-%d")} to {end.strftime("%Y-%m-%d")}'
        days = self.real_meeting.days.replace(' ', '').replace(',', '')
        days_times = f'{days}, {CourseChangesPage.meeting_time_str(self.fake_meeting)}'
        expected = f'{dates}{days_times}'.upper()
        actual = self.changes_page.current_card_schedule(self.real_section, 1, 2).upper()
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_admin_email_received(self):
        subj = f'Course Capture Admin: {self.real_section.code} schedule change'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)

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

    def test_verify_old_kaltura_series_gone(self):
        self.kaltura_page.load_event_edit_page(self.recording_sched.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_verify_new_kaltura_series_id(self):
        util.get_kaltura_id(self.recording_sched, self.term)

    def test_verify_new_kaltura_series(self):
        self.sign_up_page.load_page(self.real_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched)
        self.kaltura_page.wait_for_delete_button()
        expected = f'{self.real_section.code}, {self.real_section.number} ({self.real_section.term.name})'
        assert self.kaltura_page.visible_series_title() == expected

    def test_verify_new_kaltura_days(self):
        self.kaltura_page.open_recurrence_modal()
        mon_checked = self.kaltura_page.is_mon_checked()
        tue_checked = self.kaltura_page.is_tue_checked()
        wed_checked = self.kaltura_page.is_wed_checked()
        thu_checked = self.kaltura_page.is_thu_checked()
        fri_checked = self.kaltura_page.is_fri_checked()
        assert mon_checked if 'MO' in self.real_meeting.days else not mon_checked
        assert tue_checked if 'TU' in self.real_meeting.days else not tue_checked
        assert wed_checked if 'WE' in self.real_meeting.days else not wed_checked
        assert thu_checked if 'TH' in self.real_meeting.days else not thu_checked
        assert fri_checked if 'FR' in self.real_meeting.days else not fri_checked
        assert not self.kaltura_page.is_sat_checked()
        assert not self.kaltura_page.is_sun_checked()

    def test_verify_new_kaltura_times(self):
        start = self.fake_meeting.get_berkeley_start_time()
        visible_start = datetime.strptime(self.kaltura_page.visible_start_time(), '%I:%M %p')
        assert visible_start == start
        end = self.fake_meeting.get_berkeley_end_time()
        visible_end = datetime.strptime(self.kaltura_page.visible_end_time(), '%I:%M %p')
        assert visible_end == end
