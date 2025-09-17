"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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
import glob
from datetime import timedelta
from zipfile import ZipFile

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

    section = util.get_test_section(util.get_test_script_course('test_single_meeting_sis_changes'))
    instr = section.instructors[0]
    meeting = section.meetings[0]
    room = section.meetings[0].room
    recording_schedule = RecordingSchedule(section, meeting)

    new_meeting = Section(util.get_test_script_course('test_single_meeting_sis_changes_room_eligible')).meetings[0]
    new_meeting.room = room
    newer_meeting = Section(util.get_test_script_course('test_single_meeting_sis_changes_schedule')).meetings[0]
    newer_meeting.room = room
    newer_meeting_original_record_start = newer_meeting.meeting_schedule.record_start

    def test_setup(self):
        self.login_page.dev_auth()
        self.jobs_page.disable_all_jobs()
        self.blackouts_page.create_all_blackouts()
        self.kaltura_page.log_in_and_reset_test_data(self.calnet_page, [self.section])
        util.reset_section_and_user_test_data([self.section], [self.instr])

    def test_schedule_recordings(self):
        self.course_page.load_page(self.section)
        # TODO - admin opts course in
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()
        util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.recording_placement = RecordingPlacement.PLACE_IN_MY_MEDIA

    def test_welcome_email(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=self.instr) == 1

    def test_class_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, self.section, self.instr) == 1

    # SCHEDULED COURSE CHANGES MEETING TIME

    def test_set_new_meeting_time(self):
        util.set_course_meeting_days(self.section, self.new_meeting)
        util.set_course_meeting_time(self.section, self.new_meeting)
        self.recording_schedule.meeting = self.new_meeting

    def test_reschedule_with_new_times(self):
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()

    def test_schedule_change_email(self):
        assert util.get_sent_email_count(EmailTemplateType.SCHEDULE_CHANGE, self.section, self.instr) == 1

    # VERIFY SERIES IN DIABLO

    def test_room_new_series(self):
        self.rooms_page.navigate_to_room_page(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        self.room_page.verify_series_link_text(self.recording_schedule)

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    # VERIFY SERIES IN KALTURA

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
        assert util.get_sent_email_count(EmailTemplateType.SCHEDULE_CHANGE, self.section, self.instr) == 1

    # VERIFY COURSE HISTORY

    def test_history_new_eligible_times(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row(field='meeting_updated',
                                            old_value=None,
                                            new_value=None,
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    # EXPORT ROOM SCHEDULED EVENTS TO ICAL

    def test_ical_export_room_no_events(self):
        self.rooms_page.navigate_to_room_page(self.meeting.room)
        self.room_page.scroll_to_kaltura_events()
        date_with_no_recordings = self.recording_schedule.meeting.meeting_schedule.date_with_no_recordings(
            self.recording_schedule.section.term,
        )
        self.room_page.export_schedule_events_to_ical(events_start_date=date_with_no_recordings, events_end_date=date_with_no_recordings)
        self.room_page.verify_ical_export_error(self.room.name)

    def test_ical_export_room_events(self):
        events_start_date, events_end_date = self.recording_schedule.meeting.meeting_schedule.date_range_for_ical_export(
            self.recording_schedule.section.term,
        )
        self.room_page.export_schedule_events_to_ical(events_start_date, events_end_date)
        self.room_page.verify_ical_export_download()
        file_path = glob.glob(f'{util.default_download_dir()}/*.ics')[0]
        self.room_page.verify_ical_export_events(file_path, events_start_date, events_end_date, self.recording_schedule)
        self.i_calendar_page.load_validator_page()
        self.i_calendar_page.validate_file(file_path)

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
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()

    def test_verify_updated_kaltura_series_gone(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_run_email_job_with_null_dates(self):
        assert util.get_sent_email_count(EmailTemplateType.NO_LONGER_SCHEDULED, self.section, self.instr) == 1

    def test_no_new_schedule_update_email(self):
        assert util.get_sent_email_count(EmailTemplateType.SCHEDULE_CHANGE, self.section, self.instr) == 1

    def test_history_no_room(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row(field='not_scheduled',
                                            old_value=None,
                                            new_value='—',
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    # EXPORT ALL ROOMS SCHEDULED EVENTS TO ICAL

    def test_ical_export_no_events(self):
        self.rooms_page.load_page()
        date_with_no_recordings = self.recording_schedule.meeting.meeting_schedule.date_with_no_recordings(
            self.recording_schedule.section.term,
        )
        self.rooms_page.export_schedule_events_to_ical(events_start_date=date_with_no_recordings, events_end_date=date_with_no_recordings)
        self.rooms_page.verify_ical_export_error()

    def test_ical_export_events(self):
        events_start_date = self.newer_meeting_original_record_start
        events_end_date = events_start_date + timedelta(days=6)
        self.rooms_page.export_schedule_events_to_ical(events_start_date, events_end_date)
        self.rooms_page.verify_ical_export_download()
        zip_file_path = glob.glob(f'{util.default_download_dir()}/*.zip')[0]
        with ZipFile(zip_file_path) as zip_file:
            self.rooms_page.verify_ical_export_manifest(zip_file)
            for name in zip_file.namelist():
                if name.endswith('.ics'):
                    file_path = zip_file.extract(name, util.default_download_dir())
                    events = self.rooms_page.verify_ical_export_events(file_path, events_start_date, events_end_date)
                    if name.replace('_', ' ').startswith(self.room.name):
                        self.rooms_page.compare_ical_export_to_recording_schedule(events, events_start_date, events_end_date, self.recording_schedule)
                    self.i_calendar_page.load_validator_page()
                    self.i_calendar_page.validate_file(file_path)

    def test_reset_data(self):
        util.update_course_start_end_dates(self.section, self.meeting, self.new_meeting.meeting_schedule)
        util.set_course_meeting_days(self.section, self.new_meeting)
        util.set_course_meeting_time(self.section, self.new_meeting)
