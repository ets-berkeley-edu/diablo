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
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseInstructorChanges:

    new_instructor_test_data = util.get_test_script_course('test_course_changes_auditorium')
    section = util.get_test_section(new_instructor_test_data)
    meeting = section.meetings[0]
    new_instructor = section.instructors[0]

    old_instructor_test_data = util.get_test_script_course('test_course_changes_ineligible')
    util.get_test_section_instructor_data(old_instructor_test_data, uids_to_exclude=[new_instructor.uid])
    old_instructor = Section(old_instructor_test_data).instructors[0]

    recording_schedule = RecordingSchedule(section, meeting)
    site = CanvasSite(
        code=f'XENA Instructor Change - {section.code}',
        name=f'XENA Instructor Change - {section.code}',
        site_id=None,
    )

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

    def test_set_old_instructor_first(self):
        util.change_course_instructor(self.section, self.new_instructor, self.old_instructor)

    def test_create_course_site(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site)
        self.canvas_page.add_teacher_to_site(self.site, self.section, self.old_instructor)

    # COURSE SCHEDULED WITH INSTRUCTOR 1, WHO MODIFIES RECORDING SETTINGS

    def test_schedule_course_instr_1(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job_sequence()
        util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR

    def test_modify_recording_settings(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(self.old_instructor.uid)
        self.ouija_page.click_course_page_link(self.section)

        self.course_page.click_edit_recording_placement()
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_AUTOMATICALLY, sites=[self.site])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_AUTOMATICALLY

        self.course_page.click_rec_type_edit_button()
        self.course_page.select_rec_type(RecordingType.VIDEO_WITH_OPERATOR)
        self.course_page.save_recording_type_edits()
        self.recording_schedule.recording_type = RecordingType.VIDEO_WITH_OPERATOR

    def test_update_scheduled_recordings(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    # INSTRUCTOR 1 REPLACED BY INSTRUCTOR 2

    def test_change_to_new_instructor(self):
        util.change_course_instructor(self.section, self.old_instructor, self.new_instructor)

    def test_add_new_instructor_to_site(self):
        self.canvas_page.add_teacher_to_site(self.site, self.section, self.new_instructor)

    # UPDATE KALTURA SERIES

    def test_run_instr_change_jobs(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    # VERIFY SERIES INSTRUCTOR UPDATED BUT SETTINGS UNCHANGED

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_series_blackouts(self):
        self.room_page.verify_series_blackouts(self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    def test_verify_diablo_selected_settings(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        assert self.course_page.visible_recording_type() == self.recording_schedule.recording_type.value['desc']
        assert self.recording_schedule.recording_placement.value['desc'] in self.course_page.visible_recording_placement()
        assert self.course_page.visible_course_site_ids() == [self.site.site_id]

    def test_update_series_title_and_desc(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_update_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_kaltura_publish_type_not_updated(self):
        assert len(self.kaltura_page.publish_category_els()) == 2

    # VERIFY EMAILS

    def test_old_instructor_removed_email(self):
        self.kaltura_page.close_window_and_switch()
        assert util.get_sent_email_count(EmailTemplateType.INSTR_REMOVED, self.section, self.old_instructor) == 1

    def test_new_instructor_added_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ADDED, self.section, self.new_instructor) == 1
