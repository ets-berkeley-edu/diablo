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

import pytest
from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeC:
    """
    SCENARIO.

    - Section has two sequential meetings, one eligible and one ineligible
    - Recordings scheduled for eligible meeting
    - Ineligible meeting becomes eligible, recordings scheduled for it as well
    - Instructor is removed and then new one added
    - Start and end dates change for both meetings
    - Room is removed from first eligible meeting
    """

    # Initial course data
    test_data = util.get_test_script_course('test_weird_type_c')
    section = util.get_test_section(test_data)
    original_instructor = section.instructors[0]

    meeting_0 = section.meetings[0]
    meeting_sched_0 = meeting_0.meeting_schedule
    recording_sched_0 = RecordingSchedule(section, meeting_0)

    meeting_1 = section.meetings[1]
    meeting_sched_1 = meeting_1.meeting_schedule
    recording_sched_1 = RecordingSchedule(section, meeting_1)

    meeting_0.meeting_schedule.end_date = meeting_0.meeting_schedule.end_date - timedelta(days=15)
    meeting_1.meeting_schedule.start_date = meeting_0.meeting_schedule.end_date + timedelta(days=1)

    # Course changes data
    test_data_changes = util.get_test_script_course('test_weird_type_c_changes')
    uids_to_exclude = list(map(lambda i: i.uid, section.instructors))
    util.get_test_section_instructor_data(test_data_changes, uids_to_exclude=uids_to_exclude)
    changed_section = Section(test_data_changes)
    new_instructor = changed_section.instructors[0]
    changed_meeting_0 = changed_section.meetings[0]
    changed_meeting_sched_0 = changed_meeting_0.meeting_schedule
    changed_meeting_1 = changed_section.meetings[1]
    changed_meeting_sched_1 = changed_meeting_1.meeting_schedule
    changed_meeting_sched_0.end_date = meeting_0.meeting_schedule.end_date + timedelta(days=7)
    changed_meeting_sched_1.start_date = meeting_1.meeting_schedule.start_date + timedelta(days=7)

    def test_setup(self):
        self.login_page.load_page()
        self.login_page.dev_auth()

        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

        self.jobs_page.click_blackouts_link()
        self.blackouts_page.create_all_blackouts()

        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.section)

        util.reset_section_test_data(self.section)

        util.reset_sent_email_test_data(self.section)

    # SCHEDULE RECORDINGS

    def test_schedule_recordings(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()
        assert util.get_kaltura_id(self.recording_sched_0)
        self.recording_sched_0.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_sched_0.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    # CHECK FILTERS - SCHEDULED

    def test_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_0.room)
        self.rooms_page.click_room_link(self.meeting_0.room)
        self.room_page.wait_for_series_row(self.recording_sched_0)
        self.room_page.verify_series_link_text(self.recording_sched_0)

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_sched_0)

    def test_room_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_sched_0)

    # VERIFY SERIES IN KALTURA

    def test_series_title_and_desc(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)

    def test_series_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)

    def test_series_publication(self):
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    # VERIFY STATIC COURSE SIS DATA

    def test_course_page_link(self):
        self.kaltura_page.close_window_and_switch()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.original_instructor.uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_visible_section_sis_data(self):
        self.course_page.verify_section_sis_data(self.section)

    def test_visible_meeting_sis_data(self):
        self.course_page.verify_meeting_sis_data(self.meeting_0, idx=0)
        assert len(self.course_page.visible_meeting_days()) == 1
        assert len(self.course_page.visible_meeting_time()) == 1
        assert len(self.course_page.visible_rooms()) == 1

    def test_new_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED, self.section,
                                         self.original_instructor) == 1

    # INELIGIBLE MEETING BECOMES ELIGIBLE

    def test_ineligible_becomes_eligible(self):
        util.change_course_room(self.section, self.meeting_1, new_room=self.changed_meeting_1.room)
        self.meeting_1.room = self.changed_meeting_1.room

    def test_run_kaltura_job_ineligible_becomes_eligible(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()
        assert util.get_kaltura_id(self.recording_sched_1)
        self.recording_sched_1.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_sched_1.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    def test_meeting_0_room_page_ineligible_becomes_eligible(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_0.room)
        self.rooms_page.click_room_link(self.meeting_0.room)
        self.room_page.wait_for_series_row(self.recording_sched_0)
        self.room_page.verify_series_schedule(self.recording_sched_0)
        self.room_page.verify_series_recordings(self.recording_sched_0)

    def test_meeting_1_room_page_ineligible_becomes_eligible(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_1.room)
        self.rooms_page.click_room_link(self.meeting_1.room)
        self.room_page.wait_for_series_row(self.recording_sched_1)
        self.room_page.verify_series_schedule(self.recording_sched_1)
        self.room_page.verify_series_recordings(self.recording_sched_1)

    def test_meeting_0_course_page_ineligible_becomes_eligible(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_0, idx=0)
        self.course_page.verify_recording_placement(self.recording_sched_0)

    def test_meeting_1_course_page_ineligible_becomes_eligible(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_1, idx=1)
        self.course_page.verify_recording_placement(self.recording_sched_1)

    def test_meeting_0_kaltura_series_ineligible_becomes_eligible(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_ineligible_becomes_eligible(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    def test_no_schedule_change_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section,
                                         self.original_instructor) == 0

    def test_multi_meeting_sched_change_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_MULTIPLE_MEETING_PATTERN_CHANGE, self.section,
                                         self.original_instructor) == 1

    # INSTRUCTOR REMOVED

    def test_remove_instructor(self):
        util.change_course_instructor(self.section, old_instructor=self.original_instructor, new_instructor=None)
        self.section.instructors = []

    def test_run_kaltura_job_instr_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_meeting_0_course_page_instr_removed(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_0, idx=0)
        self.course_page.verify_recording_placement(self.recording_sched_0)

    def test_meeting_1_course_page_instr_removed(self):
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_1, idx=1)
        self.course_page.verify_recording_placement(self.recording_sched_1)

    def test_meeting_0_kaltura_series_instr_removed(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_instr_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    def test_ouija_filter_instr_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_no_instructors()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_no_instructor_removed_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_REMOVED, self.section,
                                         self.original_instructor) == 1

    # INSTRUCTOR ADDED

    def test_add_instructor(self):
        util.change_course_instructor(self.section, old_instructor=None, new_instructor=self.new_instructor)
        self.section.instructors = [self.new_instructor]

    def test_run_kaltura_job_instr_added(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_meeting_0_course_page_instr_added(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_0, idx=0)
        self.course_page.verify_recording_placement(self.recording_sched_0)

    def test_meeting_1_course_page_instr_added(self):
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_1, idx=1)
        self.course_page.verify_recording_placement(self.recording_sched_1)

    def test_meeting_0_kaltura_series_instr_added(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_instr_added(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    def test_instructor_added_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ADDED, self.section,
                                         self.new_instructor) == 1

    # START / END DATES CHANGE FOR BOTH SECTIONS

    def test_change_dates(self):
        util.update_course_start_end_dates(self.section, self.meeting_0, self.changed_meeting_sched_0)
        util.update_course_start_end_dates(self.section, self.meeting_1, self.changed_meeting_sched_1)

    def test_run_kaltura_job_date_change(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_meeting_0_room_page_date_change(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_0.room)
        self.rooms_page.click_room_link(self.meeting_0.room)
        self.room_page.wait_for_series_row(self.recording_sched_0)
        self.room_page.verify_series_schedule(self.recording_sched_0)
        self.room_page.verify_series_recordings(self.recording_sched_0)

    def test_meeting_1_room_page_date_change(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_1.room)
        self.rooms_page.click_room_link(self.meeting_1.room)
        self.room_page.wait_for_series_row(self.recording_sched_1)
        self.room_page.verify_series_schedule(self.recording_sched_1)
        self.room_page.verify_series_recordings(self.recording_sched_1)

    def test_meeting_0_course_page_date_change(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_0, idx=0)
        self.course_page.verify_recording_placement(self.recording_sched_0)

    def test_meeting_1_course_page_date_change(self):
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_1, idx=1)
        self.course_page.verify_recording_placement(self.recording_sched_1)

    def test_meeting_0_kaltura_series_date_change(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_sched_0)

    def test_meeting_1_kaltura_series_date_change(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    def test_no_email_schedule_change_date(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section,
                                         self.new_instructor) == 0

    def test_email_multi_meeting_sched_change(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_MULTIPLE_MEETING_PATTERN_CHANGE, self.section,
                                         self.new_instructor) == 1

    # ROOM REMOVED FROM FIRST ELIGIBLE SECTION

    def test_room_removed(self):
        util.change_course_room(self.section, self.meeting_0, new_room=None)

    def test_run_kaltura_job_room_removed(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_meeting_0_course_page_room_removed(self):
        self.course_page.load_page(self.section)
        assert len(self.course_page.visible_rooms()) == 1

    def test_meeting_1_course_page_room_removed(self):
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_1, idx=0)
        self.course_page.verify_recording_placement(self.recording_sched_1)

    def test_meeting_1_kaltura_series_room_removed(self):
        self.course_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_sched_1)

    def test_meeting_0_kaltura_series_room_removed(self):
        self.kaltura_page.load_event_edit_page(self.recording_sched_0.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_no_email_schedule_change_room_removed(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section,
                                         self.new_instructor) == 0

    def test_email_multi_meeting_sched_room_removed(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_MULTIPLE_MEETING_PATTERN_CHANGE, self.section,
                                         self.new_instructor) == 2

    # COURSE HISTORY

    def test_history_ineligible_becomes_eligible(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row(field='meeting_added',
                                            old_value='—',
                                            new_value=None,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_history_instructor_removed(self):
        old_val = CoursePage.expected_uids_converter([self.original_instructor])
        self.course_page.verify_history_row(field='instructor_uids',
                                            old_value=old_val,
                                            new_value=[],
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_history_instructor_added(self):
        new_val = CoursePage.expected_uids_converter([self.new_instructor])
        self.course_page.verify_history_row(field='instructor_uids',
                                            old_value=[],
                                            new_value=new_val,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_history_date_change(self):
        self.course_page.verify_history_row(field='meeting_updated',
                                            old_value=None,
                                            new_value=None,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_history_room_removed(self):
        self.course_page.verify_history_row(field='meeting_removed',
                                            old_value=None,
                                            new_value='—',
                                            requestor=None,
                                            status='succeeded',
                                            published=True)
