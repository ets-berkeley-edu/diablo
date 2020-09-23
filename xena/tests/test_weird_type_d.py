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
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.section import Section
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util

"""
SCENARIO:
- Course has two meetings at the same time, both physical and eligible for capture
- Course site is created
- Sole instructor visits sign-up page, is unable to approve
"""


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeD:

    test_data = util.get_test_script_course('test_weird_type_d')
    section = Section(test_data)
    meeting_0 = section.meetings[0]
    meeting_1 = section.meetings[1]
    recording_schedule = RecordingSchedule(section)

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_and_kaltura(self):
        if util.get_kaltura_id(self.recording_schedule, self.section.term):
            self.kaltura_page.log_in_via_calnet()
            self.kaltura_page.reset_test_data(self.term, self.recording_schedule)
        util.reset_sign_up_test_data(self.test_data)
        self.recording_schedule.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_set_course_test_sections(self):
        util.delete_sis_sections_rows(self.section)
        util.add_sis_sections_rows(self.section)

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

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

    # RUN JOBS AND VERIFY NO INVITE

    def test_no_invite_button(self):
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')
        assert not self.sign_up_page.is_present(SignUpPage.SEND_INVITE_BUTTON)

    def test_send_invite_email(self):
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_queued_emails_job()
        self.recording_schedule.approval_status = RecordingApprovalStatus.INVITED

    def test_receive_invite_email(self):
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_delivered(expected_message)

    # INSTRUCTOR LOGS IN

    def test_home_page(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
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
        instructor = self.section.instructors[0]
        instructor_names = [f'{instructor.first_name} {instructor.last_name}']
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_visible_meeting_0_days(self):
        term_dates = f'{SignUpPage.expected_term_date_str(self.meeting_0.start_date, self.meeting_0.end_date)}'
        last_date = f'(Final recording scheduled for {SignUpPage.expected_final_record_date_str(self.meeting_0, self.section.term)}.)'
        assert f'{term_dates}\n{last_date}' in self.sign_up_page.visible_meeting_days()[0]

    def test_visible_meeting_0_time(self):
        assert self.sign_up_page.visible_meeting_time()[0] == f'{self.meeting_0.start_time} - {self.meeting_0.end_time}'

    def test_visible_meeting_0_room(self):
        assert self.sign_up_page.visible_rooms()[0] == self.meeting_0.room.name

    def test_visible_meeting_1_days(self):
        term_dates = f'{SignUpPage.expected_term_date_str(self.meeting_1.start_date, self.meeting_1.end_date)}'
        last_date = f'(Final recording scheduled for {SignUpPage.expected_final_record_date_str(self.meeting_1, self.section.term)}.)'
        assert f'{term_dates}\n{last_date}' in self.sign_up_page.visible_meeting_days()[1]

    def test_visible_meeting_1_time(self):
        assert self.sign_up_page.visible_meeting_time()[1] == f'{self.meeting_1.start_time} - {self.meeting_1.end_time}'

    def test_visible_meeting_1_room(self):
        assert self.sign_up_page.visible_rooms()[1] == self.meeting_1.room.name

    # COURSE CANNOT BE SCHEDULED

    def test_no_auto_scheduling(self):
        assert self.sign_up_page.is_present(SignUpPage.NO_AUTO_SCHED_MSG)
        assert not self.sign_up_page.is_present(SignUpPage.APPROVE_BUTTON)
