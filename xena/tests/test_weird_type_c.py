"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

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

from datetime import timedelta

from flask import current_app as app
import pytest
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeC:

    # Initial course data
    test_data = util.get_test_script_course('test_weird_type_c')
    section = util.get_test_section(test_data)
    instructor_original = section.instructors[0]

    meeting_0 = section.meetings[0]
    meeting_sched_0 = meeting_0.meeting_schedule
    recording_sched_0 = RecordingSchedule(section, meeting_0)

    meeting_1 = section.meetings[1]
    meeting_sched_1 = meeting_1.meeting_schedule
    recording_sched_1 = RecordingSchedule(section, meeting_1)

    meeting_0.end_date = (meeting_0.end_date - timedelta(days=15)).strftime('%Y-%m-%d')
    meeting_1.start_date = (meeting_0.end_date - timedelta(days=14)).strftime('%Y-%m-%d')

    # Course changes data
    test_data_changes = util.get_test_script_course('test_weird_type_c_changes')
    uids_to_exclude = list(map(lambda i: i.uid, section.instructors))
    util.get_test_instructors(test_data_changes, uids_to_exclude=uids_to_exclude)
    section_changes = Section(test_data_changes)
    instructor_change = section_changes.instructors[0]
    meeting_0_changes = section_changes.meetings[0]
    meeting_sched_0_changes = meeting_0_changes.meeting_schedule
    meeting_1_changes = section_changes.meetings[1]
    meeting_sched_1_changes = meeting_1_changes.meeting_schedule
    meeting_sched_0_changes.end_date = (meeting_0.end_date + timedelta(days=7)).strftime('%Y-%m-%d')
    meeting_sched_1_changes.start_date = (meeting_1.start_date + timedelta(days=7)).strftime('%Y-%m-%d')

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_create_blackouts(self):
        self.jobs_page.click_blackouts_link()
        self.blackouts_page.delete_all_blackouts()
        self.blackouts_page.create_all_blackouts()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_sched_0)
        util.reset_section_test_data(self.section)
        self.recording_sched_0.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.section)

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()
        assert util.get_kaltura_id(self.recording_sched_0)
        self.recording_sched_0.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_sched_0.publish_type = PublishType.PUBLISH_TO_MY_MEDIA
        self.recording_sched_0.scheduling_status = RecordingSchedulingStatus.SCHEDULED

    def test_kaltura_blackouts(self):
        self.jobs_page.run_blackouts_job()

    # CHECK FILTERS - SCHEDULED

    def test_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_sched_0.scheduling_status.value

    def test_scheduled_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # VERIFY COURSE HISTORY

    # TODO - admin view of just-scheduled course

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_0.room)
        self.rooms_page.click_room_link(self.meeting_0.room)
        self.room_page.wait_for_series_row(self.recording_sched_0)

    def test_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_sched_0) == expected

    def test_room_series_start(self):
        start = self.meeting_0.expected_recording_dates(self.section.term)[0]
        assert self.room_page.series_row_start_date(self.recording_sched_0) == start

    def test_room_series_end(self):
        last_date = self.meeting_0.expected_recording_dates(self.section.term)[-1]
        assert self.room_page.series_row_end_date(self.recording_sched_0) == last_date

    def test_room_series_days(self):
        assert self.room_page.series_row_days(self.recording_sched_0) == self.meeting_sched_0.days.replace(' ', '')

    def test_series_recordings(self):
        self.room_page.expand_series_row(self.recording_sched_0)
        expected = self.meeting_sched_0.expected_recording_dates(self.section.term)
        visible = self.room_page.series_recording_start_dates(self.recording_sched_0)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        expected.reverse()
        assert visible == expected

    def test_series_blackouts(self):
        expected = self.meeting_sched_0.expected_blackout_dates(self.section.term)
        expected.sort()
        visible = self.room_page.series_recording_blackout_dates(self.recording_sched_0)
        visible.sort()
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        assert visible == expected

    # VERIFY SERIES IN KALTURA

    def test_click_series_link(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title_and_desc(self):
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)

    def test_series_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)

    def test_series_publication(self):
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    # VERIFY STATIC COURSE SIS DATA

    def test_home_page(self):
        self.kaltura_page.close_window_and_switch()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_original.uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')

    def test_sign_up_link(self):
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_course_page_link(self):
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_original.uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_visible_ccn(self):
        assert self.course_page.visible_ccn() == self.section.ccn

    def test_visible_course_title(self):
        assert self.course_page.visible_course_title() == self.section.title

    def test_visible_instructors(self):
        instructor_names = [f'{self.instructor_original.first_name} {self.instructor_original.last_name}'.strip()]
        assert self.course_page.visible_instructors() == instructor_names

    def test_visible_meeting_days(self):
        term_dates = f'{CoursePage.expected_term_date_str(self.meeting_sched_0.start_date, self.meeting_sched_0.end_date)}'
        assert term_dates in self.course_page.visible_meeting_days()[0]
        assert len(self.course_page.visible_meeting_days()) == 1

    def test_visible_meeting_time(self):
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_0.start_time} - {self.meeting_sched_0.end_time}'
        assert len(self.course_page.visible_meeting_time()) == 1

    def test_visible_room(self):
        assert self.course_page.visible_rooms()[0] == self.meeting_0.room.name
        assert len(self.course_page.visible_rooms()) == 1

    # UPDATE SETTINGS, SAVE

    def test_choose_publish_type(self):
        self.course_page.select_publish_type(PublishType.PUBLISH_AUTOMATICALLY)
        self.recording_sched_0.publish_type = PublishType.PUBLISH_AUTOMATICALLY

    def test_approve(self):
        self.course_page.click_approve_button()

    # TODO def test_confirmation(self):

    # INELIGIBLE MEETING BECOMES ELIGIBLE

    def test_ineligible_becomes_eligible(self):
        util.change_course_room(self.section, self.meeting_1, new_room=self.meeting_1_changes.room)

    def test_run_kaltura_job_ineligible_becomes_eligible(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_blackouts_job()
        self.recording_sched_1.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_sched_1.scheduling_status = RecordingSchedulingStatus.SCHEDULED
        self.recording_sched_1.publish_type = PublishType.PUBLISH_AUTOMATICALLY

    def test_run_emails_job_ineligible_becomes_eligible(self):
        self.jobs_page.run_emails_job()

    def test_meeting_0_course_page_ineligible_becomes_eligible(self):
        self.course_page.load_page(self.section)
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_0.start_date, self.meeting_sched_0.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_0.start_time} - {self.meeting_sched_0.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_0.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_0.publish_type

    def test_meeting_1_course_page_ineligible_becomes_eligible(self):
        self.course_page.load_page(self.section)
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_1.start_date, self.meeting_sched_1.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_1.start_time} - {self.meeting_sched_1.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_1.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_1.publish_type

    def test_meeting_0_kaltura_series_ineligible_becomes_eligible(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_ineligible_becomes_eligible(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    # TODO - verify course history
    # TODO - verify instructor-scheduled-email?

    # INSTRUCTOR REMOVED

    def test_remove_instructor(self):
        util.change_course_instructor(self.section, old_instructor=self.instructor_original, new_instructor=None)

    def test_run_kaltura_job_instr_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_run_emails_job_instr_removed(self):
        self.jobs_page.run_emails_job()

    def test_meeting_0_course_page_instr_removed(self):
        self.course_page.load_page(self.section)
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_0.start_date, self.meeting_sched_0.end_date)}'
        assert self.course_page.visible_instructors() == []
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_0.start_time} - {self.meeting_sched_0.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_0.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_0.publish_type

    def test_meeting_1_course_page_instr_removed(self):
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_1.start_date, self.meeting_sched_1.end_date)}'
        assert self.course_page.visible_instructors() == []
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_1.start_time} - {self.meeting_sched_1.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_1.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_1.publish_type

    def test_meeting_0_kaltura_series_instr_removed(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_instr_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    # TODO - verify course history
    # TODO - verify instructor-scheduled-email?

    # INSTRUCTOR ADDED

    def test_add_instructor(self):
        util.change_course_instructor(self.section, old_instructor=None, new_instructor=self.instructor_change)

    def test_run_kaltura_job_instr_added(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_run_emails_job_instr_added(self):
        self.jobs_page.run_emails_job()

    def test_meeting_0_course_page_instr_added(self):
        self.course_page.load_page(self.section)
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_0.start_date, self.meeting_sched_0.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_0.start_time} - {self.meeting_sched_0.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_0.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_0.publish_type

    def test_meeting_1_course_page_instr_added(self):
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_1.start_date, self.meeting_sched_1.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_1.start_time} - {self.meeting_sched_1.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_1.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_1.publish_type

    def test_meeting_0_kaltura_series_instr_added(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_instr_added(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    # START / END DATES CHANGE FOR BOTH SECTIONS

    def test_change_dates(self):
        util.update_course_start_end_dates(self.section, self.meeting_0, self.meeting_sched_0_changes)
        util.update_course_start_end_dates(self.section, self.meeting_1, self.meeting_sched_1_changes)

    def test_run_kaltura_job_date_change(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_blackouts_job()

    def test_run_emails_job_date_change(self):
        self.jobs_page.run_emails_job()

    def test_meeting_0_course_page_date_change(self):
        self.course_page.load_page(self.section)
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_0.start_date, self.meeting_sched_0.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_0.start_time} - {self.meeting_sched_0.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_0.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_0.publish_type

    def test_meeting_1_course_page_date_change(self):
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_1.start_date, self.meeting_sched_1.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_1.start_time} - {self.meeting_sched_1.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_1.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_1.publish_type

    def test_meeting_0_kaltura_series_date_change(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_date_change(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    # TODO - Verify course history
    # TODO - Verify email sent

    # ROOM REMOVED FROM FIRST ELIGIBLE SECTION

    def test_room_removed(self):
        util.change_course_room(self.section, self.meeting_0, new_room=None)

    def test_run_kaltura_job_room_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_blackouts_job()

    def test_run_emails_job_room_removed(self):
        self.jobs_page.run_emails_job()

    def test_meeting_1_course_page_room_removed(self):
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        term_dates_0 = f'{CoursePage.expected_term_date_str(self.meeting_sched_1.start_date, self.meeting_sched_1.end_date)}'
        assert self.course_page.visible_instructors() == instructor_names
        assert term_dates_0 in self.course_page.visible_meeting_days()[0]
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_sched_1.start_time} - {self.meeting_sched_1.end_time}'
        assert self.course_page.visible_rooms()[0] == self.meeting_1.room.name
        assert self.course_page.scheduled_publish_type() == self.recording_sched_1.publish_type

    def test_meeting_0_course_page_room_removed(self):
        self.course_page.load_page(self.section)
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.section.instructors]
        assert self.course_page.visible_instructors() == instructor_names
        assert len(self.course_page.visible_rooms()) == 1

    def test_meeting_1_kaltura_series_room_removed(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    def test_meeting_0_kaltura_series_room_removed(self):
        self.kaltura_page.load_event_edit_page(self.recording_sched_0.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    # TODO - Verify course history
    # TODO - Verify email sent
