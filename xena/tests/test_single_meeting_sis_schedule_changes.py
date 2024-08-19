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

import pytest
from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseScheduleChanges:
    """
    SCENARIO.

    - Section has one instructor and one meeting
    - Recordings scheduled
    - Meeting days and times change, series updated
    - SIS schedule vanishes altogether, recordings unscheduled
    """

    section = util.get_test_section(util.get_test_script_course('test_course_changes_auditorium'))
    instr = section.instructors[0]
    meeting = section.meetings[0]
    room = section.meetings[0].room
    recording_schedule = RecordingSchedule(section, meeting)

    new_meeting = Section(util.get_test_script_course('test_course_changes_eligible')).meetings[0]
    new_meeting.room = room
    newer_meeting = Section(util.get_test_script_course('test_course_changes_faker')).meetings[0]
    newer_meeting.room = room

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

    def test_schedule_recordings(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()
        util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    def test_welcome_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED, self.section, self.instr) == 1

    # SCHEDULED COURSE CHANGES MEETING TIME

    def test_set_new_meeting_time(self):
        util.set_course_meeting_days(self.section, self.new_meeting)
        util.set_course_meeting_time(self.section, self.new_meeting)
        self.recording_schedule.meeting = self.new_meeting

    def test_reschedule_with_new_times(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_schedule_change_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section, self.instr) == 1

    def test_room_new_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.room)
        self.rooms_page.click_room_link(self.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        self.room_page.verify_series_link_text(self.recording_schedule)

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    def test_series_title_and_desc(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.new_meeting)

    def test_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.new_meeting)

    def test_series_publish_status(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_kaltura_course_site(self):
        self.kaltura_page.verify_site_categories([])

    def test_email_instr_new_meeting(self):
        self.kaltura_page.close_window_and_switch()
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section, self.instr) == 1

    def test_history_new_eligible_times(self):
        old_val = None
        new_val = None
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row('meeting_updated', old_val, new_val, None, 'succeeded', published=True)

    # SCHEDULED COURSE MEETING START/END AND MEETING DAYS/TIMES CHANGE TO NULL

    def test_set_null_schedule(self):
        self.newer_meeting.meeting_schedule.start_date = None
        self.newer_meeting.meeting_schedule.end_date = None
        self.newer_meeting.meeting_schedule.days = None
        self.newer_meeting.meeting_schedule.start_time = None
        self.newer_meeting.meeting_schedule.end_time = None
        util.update_course_start_end_dates(self.section, self.meeting, self.newer_meeting.meeting_schedule)
        util.set_course_meeting_days(self.section, self.newer_meeting)
        util.set_course_meeting_time(self.section, self.newer_meeting)
        self.recording_schedule.meeting = self.newer_meeting

    def test_unschedule_with_null_schedule(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_verify_updated_kaltura_series_gone(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_run_email_job_with_null_dates(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_COURSE_CANCELLED, self.section, self.instr) == 1

    def test_no_new_schedule_update_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section, self.instr) == 1

    def test_history_no_room(self):
        old_val = None
        new_val = '—'
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row('not_scheduled', old_val, new_val, None, 'succeeded', published=True)

    def test_reset_data(self):
        util.update_course_start_end_dates(self.section, self.meeting, self.new_meeting.meeting_schedule)
        util.set_course_meeting_days(self.section, self.new_meeting)
        util.set_course_meeting_time(self.section, self.new_meeting)
