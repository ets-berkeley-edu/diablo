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

from flask import current_app as app
import pytest
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseRoomChanges:
    real_test_data = util.get_test_script_course('test_course_changes_real')
    fake_test_data = util.get_test_script_course('test_course_changes_fake')
    faker_test_data = util.get_test_script_course('test_course_changes_faker')
    fakest_test_data = util.get_test_script_course('test_course_changes_fakest')
    real_section = util.get_test_section(real_test_data)
    real_meeting = real_section.meetings[0]
    fake_section = Section(fake_test_data)
    fake_meeting = fake_section.meetings[0]
    faker_section = Section(faker_test_data)
    faker_meeting = faker_section.meetings[0]
    fakest_section = Section(fakest_test_data)
    fakest_meeting = fakest_section.meetings[0]
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

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
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

    # SCHEDULED COURSE MOVES TO ANOTHER ELIGIBLE ROOM

    def test_move_to_alt_eligible_room(self):
        util.set_meeting_location(self.real_section, self.fakest_meeting)

    def test_run_admin_email_job_alt_eligible_room(self):
        self.jobs_page.run_admin_emails_job()

    def test_run_instr_email_job_alt_eligible_room(self):
        self.jobs_page.run_instructor_emails_job()

    def test_run_queued_email_job_alt_eligible_room(self):
        self.jobs_page.run_queued_emails_job()

    def test_changes_page_summary_alt_eligible_room(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)
        expected = 'Room is obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.real_section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_old_elig_room(self):
        expected = f'{self.real_meeting.room.name}'
        actual = self.changes_page.scheduled_card_old_room(self.real_section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_new_elig_room(self):
        expected = f'{self.fakest_meeting.room.name}'
        actual = self.changes_page.current_card_schedule(self.real_section, list_node=None, detail_node=None)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    # SCHEDULED COURSE MOVES TO INELIGIBLE ROOM

    def test_move_to_ineligible_room(self):
        util.set_meeting_location(self.real_section, self.fake_meeting)

    def test_run_admin_email_job_ineligible_room(self):
        self.jobs_page.run_admin_emails_job()

    def test_run_instr_email_job_ineligible_room(self):
        self.jobs_page.run_instructor_emails_job()

    def test_run_queued_email_job_ineligible_room(self):
        self.jobs_page.run_queued_emails_job()

    def test_changes_page_summary(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_course_row(self.real_section)
        expected = 'Room is obsolete.'
        actual = self.changes_page.scheduled_card_summary(self.real_section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_old_room(self):
        expected = f'{self.real_meeting.room.name}'
        actual = self.changes_page.scheduled_card_old_room(self.real_section)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_changes_page_new_room(self):
        expected = f'{self.fake_meeting.room.name}'
        actual = self.changes_page.current_card_schedule(self.real_section, list_node=None, detail_node=None)
        app.logger.info(f'Expecting: {expected}')
        app.logger.info(f'Actual: {actual}')
        assert expected in actual

    def test_admin_unsched_ineligible_room(self):
        self.sign_up_page.load_page(self.real_section)
        self.sign_up_page.confirm_unscheduling_ineligible(self.recording_sched)

    def test_changes_page_ineligible_room_unsched(self):
        self.sign_up_page.click_course_changes_link()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.real_section)

    def test_no_kaltura_series_ineligible_room(self):
        self.kaltura_page.load_event_edit_page(self.recording_sched.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_admin_email_ineligible_room(self):
        subj = f'Course Capture Admin: {self.real_section.code} has moved to {self.fake_meeting.room.name}'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_instructor_email_ineligible_room(self):
        subj = f'Your course {self.real_section.code} is no longer eligible for Course Capture'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_instructor_email_alt_eligible_room(self):
        subj = f'Your course {self.real_section.code} is no longer eligible for Course Capture'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert len(self.email_page.message_rows(email)) == 1

    # ROOM REMOVED

    def test_reset_data_null_test(self):
        util.reset_sign_up_test_data(self.real_section)
        self.recording_sched.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_sched.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_sign_up_null_test(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.real_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.real_section)
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()

    def test_schedule_recordings_null_test(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched, self.term)

    def test_move_to_null_room(self):
        self.faker_meeting.room = None
        util.change_course_room(self.real_section, old_room=self.real_meeting.room, new_room=None)

    def test_run_admin_email_job_null_room(self):
        self.jobs_page.load_page()
        self.jobs_page.run_admin_emails_job()

    def test_run_instr_email_job_null_room(self):
        self.jobs_page.run_instructor_emails_job()

    def test_run_queued_email_job_null_room(self):
        self.jobs_page.run_queued_emails_job()

    def test_null_room_changes_page_summary(self):
        self.jobs_page.click_course_changes_link()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.real_section)
