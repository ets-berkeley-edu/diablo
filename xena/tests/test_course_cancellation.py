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

from flask import current_app as app
import pytest
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.pages.ouija_board_page import OuijaBoardPage
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseCancellation:

    # INITIALIZE TESTS

    test_data = util.get_test_script_course('test_course_cancellation')
    section = util.get_test_section(test_data)
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section)

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)
        util.reset_sign_up_test_data(self.section)
        self.recording_schedule.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_emails_pre_run(self):
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    # COURSE IS CANCELLED BEFORE SIGN-UP

    def test_deleted_pre_signup(self):
        util.delete_section(self.section)

    def test_deleted_pre_signup_no_search_result(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is False

    def test_deleted_pre_sign_up_no_admin_approve(self):
        self.sign_up_page.load_page(self.section)
        assert self.sign_up_page.is_canceled()
        assert not self.sign_up_page.is_present(SignUpPage.APPROVE_BUTTON)
        assert not self.sign_up_page.is_present(SignUpPage.SELECT_PUBLISH_TYPE_INPUT)
        assert not self.sign_up_page.is_present(SignUpPage.SEND_INVITE_BUTTON)

    def test_deleted_pre_signup_no_teacher_result(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_title_contains('Eligible for Capture')
        assert not self.ouija_page.is_present(OuijaBoardPage.course_row_link_locator(self.section))

    def test_deleted_pre_signup_no_teacher_approve(self):
        self.sign_up_page.load_page(self.section)
        assert self.sign_up_page.is_canceled()
        assert not self.sign_up_page.is_present(SignUpPage.APPROVE_BUTTON)
        assert not self.sign_up_page.is_present(SignUpPage.SELECT_PUBLISH_TYPE_INPUT)

    # COURSE IS RESTORED AND SCHEDULED

    def test_restored_pre_sign_up(self):
        util.restore_section(self.section)

    def test_approve(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()
        msg = 'This course is currently queued for scheduling. Recordings will be scheduled in an hour or less. Approved by you.'
        self.sign_up_page.wait_for_approvals_msg(msg)
        self.recording_schedule.recording_type = RecordingType.SCREENCAST
        self.recording_schedule.publish_type = PublishType.BCOURSES
        self.recording_schedule.approval_status = RecordingApprovalStatus.APPROVED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.QUEUED_FOR_SCHEDULING

    def test_kaltura_job(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_schedule_id(self):
        util.get_kaltura_id(self.recording_schedule, self.term)

    def test_kaltura_blackouts(self):
        self.jobs_page.run_blackouts_job()

    # COURSE IS CANCELLED AGAIN

    def test_delete_scheduled(self):
        util.delete_section(self.section)

    def test_course_page_cancelled(self):
        self.sign_up_page.load_page(self.section)
        assert self.sign_up_page.is_canceled()

    def test_course_changes(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_results()
        assert self.changes_page.is_course_row_present(self.section)
        assert self.changes_page.is_course_canceled(self.section)

    def test_search_cancelled(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section) is True
        assert self.ouija_page.course_row_status_el(self.section).text.strip() == 'Canceled'

    def test_emails_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()

    # UNSCHEDULE CANCELED COURSE

    def test_admin_unsched_canceled(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.confirm_unscheduling_ineligible(self.recording_schedule)

    def test_changes_page_canceled_unsched(self):
        self.sign_up_page.click_course_changes_link()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.section)

    def test_no_kaltura_series_canceled_unsched(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_unsched_again_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section) is False

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_admin_email_canceled_ineligible(self):
        subj = f'Course Capture Admin: {self.section.code} has moved to CANCELED'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)

    @pytest.mark.skipif(app.config['SKIP_EMAILS'], reason='Check email')
    def test_instructor_email_canceled_ineligible(self):
        subj = f'Your course {self.section.code} is no longer eligible for Course Capture'
        email = Email(msg_type=None, subject=subj, sender=None)
        assert self.email_page.is_message_delivered(email)
