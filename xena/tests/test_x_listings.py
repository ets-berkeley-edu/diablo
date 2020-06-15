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
from xena.models.async_job import AsyncJob
from xena.models.email import Email
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCrossListings:

    test_data = util.parse_course_test_data()[7]
    section = Section(test_data)
    x_listings = section.listings
    recording_schedule = RecordingSchedule(section)

    # DELETE PRE-EXISTING DATA AND MAKE SURE THE CROSS-LISTED COURSE IS IN A ROOM WITH A KALTURA RESOURCE

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_queued_emails_job()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_kaltura_series(self):
        self.kaltura_page.log_in_via_calnet()
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)

    def test_delete_old_diablo_data(self):
        util.reset_sign_up_test_data(self.test_data)
        self.recording_schedule.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_move_course_location(self):
        util.set_course_room(self.section)

    def test_delete_old_email(self):
        self.email_page.log_in()
        self.email_page.delete_all_messages()

    # INSTRUCTORS FOLLOW SIGN UP WORKFLOW

    def test_instructor_home(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_course_result(self.section)
        for listing in self.section.listings:
            assert listing.code in self.ouija_page.course_row_code_el(self.section).get_attribute('innerText')

    def test_hit_listing(self):
        self.sign_up_page.hit_url(self.section.term.id, self.section.listings[0].ccn)
        self.sign_up_page.wait_for_404()

    def test_view_sign_up_page(self):
        self.ouija_page.load_instructor_view()
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')
        assert self.sign_up_page.visible_heading() == f'{self.section.code}, {self.section.number}'

    def test_verify_sign_up_page_listings(self):
        expected = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        expected.sort()
        visible = self.sign_up_page.visible_cross_listing_codes()
        visible.sort()
        assert visible == expected

    def test_approve_inst_1(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()

    def test_approve_inst_2(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth(self.section.instructors[1].uid)
        self.ouija_page.click_sign_up_page_link(self.section)
        self.sign_up_page.select_publish_type(PublishType.KALTURA.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()
        self.recording_schedule.approval_status = RecordingApprovalStatus.APPROVED

    def test_schedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()
        util.wait_for_kaltura_id(self.recording_schedule, self.term)

    def test_click_series_link(self):
        self.sign_up_page.load_page(self.section)
        self.sign_up_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title(self):
        listing_codes = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        listing_codes.append(f'{self.section.code}, {self.section.number}')
        for code in listing_codes:
            assert code in self.kaltura_page.visible_series_title()

    # VERIFY AUTO-EMAILS

    def test_send_emails(self):
        self.jobs_page.load_page()
        self.jobs_page.run_invitations_job()
        self.jobs_page.run_instructor_emails_job()
        self.jobs_page.run_queued_emails_job()

    def test_invite_inst_1(self):
        self.recording_schedule.approval_status = RecordingApprovalStatus.INVITED
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_delivered(expected_message)

    def test_invite_inst_2(self):
        subj = f'Invitation {self.section.term.name} {self.section.code} (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_present(expected_message)

    def test_no_dupe_invite_inst_1(self):
        subj = f'Invitation {self.section.term.name} {self.section.listings[0].code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    def test_awaiting_approval_inst_1(self):
        subj = f'Course Capture: {self.section.code} waiting on approval (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_present(expected_message)

    def test_no_awaiting_approval_inst_2(self):
        subj = f'Course Capture: {self.section.code} waiting on approval (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    def test_no_dupe_awaiting_approval_inst_1(self):
        subj = f'Course Capture: {self.section.listings[0].code} waiting on approval (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    def test_notify_of_changes_inst_1(self):
        subj = f'Changes to your Course Capture settings for {self.section.code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_present(expected_message)

    def test_no_notify_of_changes_inst_2(self):
        subj = f'Changes to your Course Capture settings for {self.section.code} (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    def test_no_dupe_notify_of_changes_inst_1(self):
        subj = f'Changes to your Course Capture settings for {self.section.listings[0].code} (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)

    def test_schedule_conf_inst_1(self):
        subj = f'Your course, {self.section.code}, has been scheduled for Course Capture (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_present(expected_message)

    def test_schedule_conf_inst_2(self):
        subj = f'Your course, {self.section.code}, has been scheduled for Course Capture (To: {self.section.instructors[1].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert self.email_page.is_message_present(expected_message)

    def test_no_dupe_schedule_conf_inst_1(self):
        subj = f'Your course, {self.section.listings[0].code}, has been scheduled for Course Capture (To: {self.section.instructors[0].email})'
        expected_message = Email(msg_type=None, sender=None, subject=subj)
        assert not self.email_page.is_message_present(expected_message)
