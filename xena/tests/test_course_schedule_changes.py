
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
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseScheduleChanges:

    section = util.get_test_section(util.get_test_script_course('test_course_changes_real'))
    instr = section.instructors[0]
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section, meeting)

    new_meeting = Section(util.get_test_script_course('test_course_changes_fake')).meetings[0]
    newer_meeting = Section(util.get_test_script_course('test_course_changes_faker')).meetings[0]

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)
        util.reset_section_test_data(self.section)
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_emails_pre_run(self):
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.section)

    def test_semester_start(self):
        self.jobs_page.run_semester_start_job()
        util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.SCHEDULED
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.publish_type = PublishType.PUBLISH_TO_MY_MEDIA

    def test_run_email_job_post_scheduling(self):
        self.jobs_page.run_emails_job()

    # SCHEDULED COURSE CHANGES MEETING TIME

    def test_set_new_meeting_time(self):
        util.set_course_meeting_time(self.section, self.new_meeting)

    def test_reschedule_with_new_times(self):
        self.jobs_page.load_page()
        # TODO - run updates job
        self.jobs_page.run_kaltura_job()

    def test_verify_old_kaltura_series_gone(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_get_new_kaltura_series_id(self):
        util.get_kaltura_id(self.recording_schedule)

    def test_room_new_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.new_meeting.room)
        self.rooms_page.click_room_link(self.new_meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule) == expected

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.section, self.new_meeting, self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.section, self.new_meeting, self.recording_schedule)

    def test_series_blackouts(self):
        self.room_page.verify_series_blackouts(self.section, self.new_meeting, self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.section, self.new_meeting, self.recording_schedule)

    def test_click_series_link(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title_and_desc(self):
        self.kaltura_page.verify_title_and_desc(self.section, self.new_meeting)

    def test_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.new_meeting)

    def test_series_publish_status(self):
        assert self.kaltura_page.is_private()

    def test_kaltura_course_site(self):
        assert len(self.kaltura_page.publish_category_els()) == 0

    def test_email_instr_new_meeting(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.run_emails_job()
        assert len(util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section, self.instr)) == 1

    # TODO - verify history

    # SCHEDULED COURSE MEETING START/END AND MEETING DAYS/TIMES CHANGE TO NULL

    def test_set_null_schedule(self):
        self.newer_meeting.meeting_schedule.start_date = None
        self.newer_meeting.meeting_schedule.end_date = None
        self.newer_meeting.meeting_schedule.days = None
        self.newer_meeting.meeting_schedule.start_time = None
        self.newer_meeting.meeting_schedule.end_time = None
        util.update_course_start_end_dates(self.section, self.meeting.room, self.newer_meeting.meeting_schedule)
        util.set_course_meeting_days(self.section, self.newer_meeting)
        util.set_course_meeting_time(self.section, self.newer_meeting)

    def test_unschedule_with_null_schedule(self):
        self.jobs_page.load_page()
        # TODO - run updates job
        self.jobs_page.run_kaltura_job()

    def test_verify_updated_kaltura_series_gone(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_verify_no_new_kaltura_series_id(self):
        assert not util.get_kaltura_id(self.recording_schedule)

    def test_run_email_job_with_null_dates(self):
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()
        # TODO - which email does the instructor get?  course cancelled?  schedule change?

    # TODO - verify history
