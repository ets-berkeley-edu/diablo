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

"""
SCENARIO:
- Course has two meetings at the same time, one physical and one online
- Sole instructor visits sign-up page, approves
- Recordings scheduled
- Instructor, physical room, and schedule then change
"""


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeB:

    # Initial course data
    test_data = util.get_test_script_course('test_weird_type_b')
    section = util.get_test_section(test_data)
    meeting_physical = section.meetings[0]
    meeting_online = section.meetings[1]
    original_instructor = section.instructors[0]
    original_room = meeting_physical.room
    meeting_schedule = meeting_physical.meeting_schedule
    recording_schedule = RecordingSchedule(section, meeting_physical)

    # Course changes data
    test_data_changes = util.get_test_script_course('test_weird_type_b_changes')
    uids_to_exclude = list(map(lambda i: i.uid, section.instructors))
    util.get_test_section_instructor_data(test_data_changes, uids_to_exclude=uids_to_exclude)
    changes = Section(test_data_changes)
    meeting_changes = changes.meetings[0]

    new_instructor = changes.instructors[0]
    new_room = meeting_changes.room
    # Set changed physical meeting start/end dates relative to original dates
    schedule_change = meeting_changes.meeting_schedule
    schedule_change.start_date = meeting_schedule.end_date - timedelta(days=14)
    schedule_change.end_date = meeting_schedule.end_date - timedelta(days=7)

    def test_setup(self):
        self.login_page.load_page()
        self.login_page.dev_auth()

        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

        self.jobs_page.click_blackouts_link()
        self.blackouts_page.delete_all_blackouts()
        self.blackouts_page.create_all_blackouts()

        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.section)

        util.reset_section_test_data(self.section)

        util.reset_sent_email_test_data(self.section)

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job_sequence()
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    # CHECK FILTERS - SCHEDULED

    def test_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_sched_status(self):
        visible_status = self.ouija_page.visible_course_row_sched_status(self.section)
        assert visible_status == 'Scheduled'

    def test_scheduled_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # INSTRUCTOR LOGS IN

    def test_home_page(self):
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')

    def test_course_page_link(self):
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    # VERIFY STATIC COURSE SIS DATA - only the eligible meeting is displayed

    def test_visible_section_sis_data(self):
        self.course_page.verify_section_sis_data(self.section)

    def test_visible_meeting_sis_data(self):
        self.course_page.verify_meeting_sis_data(self.meeting_physical, idx=0)
        assert len(self.course_page.visible_rooms()) == 1
        assert len(self.course_page.visible_meeting_days()) == 1
        assert len(self.course_page.visible_meeting_time()) == 1

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_rooms_link()
        self.rooms_page.find_room(self.original_room)
        self.rooms_page.click_room_link(self.original_room)
        self.room_page.wait_for_series_row(self.recording_schedule)
        self.room_page.verify_series_link_text(self.recording_schedule)

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule)

    def test_room_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    # VERIFY SERIES IN KALTURA

    def test_kaltura_series_title(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_physical)

    def test_kaltura_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_kaltura_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_physical)

    # INSTRUCTOR REMOVED

    def test_remove_instructor(self):
        self.kaltura_page.close_window_and_switch()
        util.change_course_instructor(self.section, old_instructor=self.original_instructor, new_instructor=None)
        self.section.instructors = []

    def test_run_kaltura_job_instr_removed(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_course_page_instr_removed(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_physical, idx=0)
        self.course_page.verify_recording_placement(self.recording_schedule)

    def test_series_title_and_desc_instr_removed(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_physical)

    def test_series_collab_instr_removed(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule_instr_removed(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_physical)

    def test_series_publish_status_instr_removed(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_no_instructor_removed_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_REMOVED, self.section) == 0

    # INSTRUCTOR ADDED

    def test_add_instructor(self):
        self.kaltura_page.close_window_and_switch()
        util.change_course_instructor(self.section, old_instructor=None, new_instructor=self.new_instructor)
        self.section.instructors = [self.new_instructor]

    def test_run_kaltura_job_instr_added(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_course_page_instr_added(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_physical, idx=0)
        self.course_page.verify_recording_placement(self.recording_schedule)

    def test_series_title_and_desc_instr_added(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_physical)

    def test_series_collab_instr_added(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule_instr_added(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_physical)

    def test_series_publish_status_instr_added(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_instructor_added_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ADDED, self.section, self.new_instructor) == 1

    # START / END DATES CHANGE FOR ELIGIBLE SECTION

    def test_change_dates(self):
        self.kaltura_page.close_window_and_switch()
        util.update_course_start_end_dates(self.section, self.meeting_physical, self.schedule_change)

    def test_run_kaltura_job_new_dates(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_course_page_new_dates(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_physical, idx=0)
        self.course_page.verify_recording_placement(self.recording_schedule)

    def test_series_title_and_desc_new_dates(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_changes)

    def test_series_collab_new_dates(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule_new_dates(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_changes)

    def test_series_publish_status_new_dates(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_schedule_change_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section,
                                         self.new_instructor) == 1

    # ROOM REMOVED

    def test_remove_room(self):
        self.kaltura_page.close_window_and_switch()
        util.change_course_room(self.section, self.meeting_physical, new_room=None)

    def test_run_kaltura_job_room_removed(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_course_page_room_removed(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_present(CoursePage.NOT_ELIGIBLE_MSG)

    def test_series_canceled_room_removed(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_room_no_longer_eligible_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ROOM_CHANGE_INELIGIBLE, self.section,
                                         self.new_instructor) == 1

    # ROOM ADDED

    def test_add_room(self):
        util.change_course_room(self.section, self.meeting_physical, new_room=self.new_room)
        self.meeting_physical.room = self.new_room

    def test_run_kaltura_job_room_added(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_course_page_room_added(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)
        self.course_page.verify_meeting_sis_data(self.meeting_physical, idx=0)
        self.course_page.verify_recording_placement(self.recording_schedule)

    def test_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED, self.section,
                                         self.new_instructor) == 1

    # COURSE HISTORY

    def test_course_history_instructor_removed(self):
        old_val = CoursePage.expected_uids_converter([self.original_instructor])
        new_val = []
        self.course_page.verify_history_row(field='instructor_uids',
                                            old_value=old_val,
                                            new_value=new_val,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_course_history_instructor_added(self):
        old_val = []
        new_val = CoursePage.expected_uids_converter([self.new_instructor])
        self.course_page.verify_history_row(field='instructor_uids',
                                            old_value=old_val,
                                            new_value=new_val,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_course_history_dates_changed(self):
        self.course_page.verify_history_row(field='meeting_updated',
                                            old_value=None,
                                            new_value=None,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_course_history_room_removed(self):
        self.course_page.verify_history_row(field='room_not_eligible',
                                            old_value=None,
                                            new_value=None,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)
