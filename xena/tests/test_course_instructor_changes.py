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
from xena.models.canvas_site import CanvasSite
from xena.models.email_template_type import EmailTemplateType
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseInstructorChanges:

    instr_2_test_data = util.get_test_script_course('test_course_changes_real')
    section = util.get_test_section(instr_2_test_data)
    meeting = section.meetings[0]
    instr_2 = section.instructors[0]

    instr_1_test_data = util.get_test_script_course('test_course_changes_fake')
    util.get_test_instructors(instr_1_test_data, uids_to_exclude=[instr_2.uid])
    instr_1 = Section(instr_1_test_data).instructors[0]

    recording_sched = RecordingSchedule(section)
    site = CanvasSite(
        code=f'XENA Instructor Change - {section.code}',
        name=f'XENA Instructor Change - {section.code}',
        site_id=None,
    )

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_sched)
        util.reset_section_test_data(self.section)
        self.recording_sched.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_emails_pre_run(self):
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.section)

    def test_set_instr_1(self):
        util.change_course_instructor(self.section, self.instr_2, self.instr_1)

    # TODO - create course site, manually adding instructor 1 to the site

    # COURSE SCHEDULED WITH INSTRUCTOR 1, WHO MODIFIES RECORDING SETTINGS

    def test_schedule_course_instr_1(self):
        self.jobs_page.run_semester_start_job()
        util.get_kaltura_id(self.recording_sched, self.term)
        self.recording_sched.scheduling_status = RecordingSchedulingStatus.SCHEDULED

    def test_modify_recording_settings(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instr_1.uid)
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.select_publish_type(PublishType.PUBLISH_AUTOMATICALLY.value)
        self.course_page.select_recording_type(RecordingType.VIDEO_WITH_OPERATOR.value)
        # TODO - add course site
        self.course_page.click_approve_button()

    def test_update_scheduled_recordings(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    # INSTRUCTOR 1 REPLACED BY INSTRUCTOR 2

    def test_change_to_instr_2(self):
        util.change_course_instructor(self.section, self.instr_1, self.instr_2)

    # UPDATE KALTURA SERIES

    def test_run_instr_change_jobs(self):
        # TODO = run updates job
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    # VERIFY SERIES INSTRUCTOR UPDATED BUT SETTINGS UNCHANGED

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.section, self.meeting, self.recording_schedule)

    def test_series_blackouts(self):
        self.room_page.verify_series_blackouts(self.section, self.meeting, self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.section, self.meeting, self.recording_schedule)

    def test_verify_diablo_selected_settings(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        # TODO - verify recording type
        # TODO - verify publish type
        # TODO - verify selected course site

    def test_update_series_title_and_desc(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_update_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_kaltura_publish_type_not_updated(self):
        assert self.kaltura_page.is_published()
        assert len(self.kaltura_page.publish_category_els()) == 0
        self.kaltura_page.close_window_and_switch()

    # VERIFY EMAILS

    def test_instr_1_removed_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_REMOVED, self.section, self.instr_1) == 1

    def test_instr_2_added_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ADDED, self.section, self.instr_2) == 1
