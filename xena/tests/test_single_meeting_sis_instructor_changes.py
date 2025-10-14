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

import pytest

from xena.models.canvas_site import CanvasSite
from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.models.section import Section
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseInstructorChanges:
    """
    SCENARIO.

    - Section has one meeting, one instructor, and a course site
    - Instructor opts in, and recordings are scheduled
    - Instructor adds operator and auto-publish, adding site
    - Instructor is replaced by new Instructor
    - Recordings are unscheduled
    - New instructor opts in, recordings scheduled with default settings
    """

    new_instructor_test_data = util.get_test_script_course('test_single_meeting_sis_changes')
    section = util.get_test_section(new_instructor_test_data)
    meeting = section.meetings[0]
    new_instructor = section.instructors[0]

    old_instructor_test_data = util.get_test_script_course('test_single_meeting_sis_changes_room_ineligible')
    util.get_test_section_instructor_data(old_instructor_test_data, uids_to_exclude=[new_instructor.uid])
    old_instructor = Section(old_instructor_test_data).instructors[0]

    recording_schedule = RecordingSchedule(section, meeting)
    site = CanvasSite(
        code=f'XENA Instructor Change - {section.code}',
        name=f'XENA Instructor Change - {section.code}',
        site_id=None,
    )

    def test_setup(self):
        self.login_page.dev_auth()
        self.jobs_page.disable_all_jobs()
        self.blackouts_page.create_all_blackouts()
        self.kaltura_page.log_in_and_reset_test_data(self.calnet_page, [self.section])
        util.reset_section_and_user_test_data([self.section], [self.old_instructor, self.new_instructor])

    def test_set_old_instructor_first(self):
        util.change_course_instructor(self.section, self.new_instructor, self.old_instructor)
        self.section.instructors = [self.old_instructor]

    def test_schedule_update(self):
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()

    def test_create_course_site(self):
        self.canvas_page.create_site(self.section, self.site, self.calnet_page)
        self.canvas_page.add_user_to_site(self.site, self.old_instructor, 'TA')

    # COURSE SCHEDULED WITH INSTRUCTOR 1, WHO MODIFIES RECORDING SETTINGS

    def test_old_instructor_opt_in(self):
        self.login_page.dev_auth(self.old_instructor.uid)
        self.courses_page.click_course_page_link(self.section)
        self.course_page.instructor_opt_in_section(self.section, self.old_instructor)

    def test_old_instructor_recordings_scheduled(self):
        self.login_page.dev_auth()
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()
        util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_placement = RecordingPlacement.PLACE_IN_MY_MEDIA
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR

    def test_old_instructor_modify_recording_settings(self):
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

    def test_old_instructor_update_scheduled_recordings(self):
        self.login_page.dev_auth()
        self.jobs_page.run_kaltura_job_sequence()

    def test_series_title_and_desc(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting)

    def test_series_publish_status(self):
        self.kaltura_page.wait_for_publish_category_el()
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_update_kaltura_course_site(self):
        self.kaltura_page.verify_site_categories([self.site])

    # INSTRUCTOR 1 REPLACED BY INSTRUCTOR 2

    def test_change_to_new_instructor(self):
        util.change_course_instructor(self.section, self.old_instructor, self.new_instructor)
        self.section.instructors = [self.new_instructor]

    def test_recordings_unscheduled(self):
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()
        assert not util.get_kaltura_id(self.recording_schedule)

    def test_old_instructor_removed_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTRUCTORS_REMOVED, self.section, self.old_instructor) == 1

    def test_new_instructor_class_eligible_email(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=self.new_instructor) == 1
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, self.section, self.new_instructor) == 1

    def test_new_instructor_opts_in(self):
        self.login_page.dev_auth(self.new_instructor.uid)
        self.courses_page.click_course_page_link(self.section)
        self.course_page.instructor_opt_in_section(self.section, self.new_instructor)

    # UPDATE KALTURA SERIES

    def test_run_instr_change_jobs(self):
        self.login_page.dev_auth()
        self.jobs_page.run_kaltura_job_sequence()
        assert util.get_kaltura_id(self.recording_schedule)

    def test_new_instructor_class_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, self.section, self.new_instructor) == 1

    # VERIFY SERIES INSTRUCTOR UPDATED AND SETTINGS PRESERVED

    def test_room_series(self):
        self.rooms_page.navigate_to_room_page(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    def test_verify_diablo_selected_settings(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.verify_recording_type(self.recording_schedule)
        self.course_page.verify_recording_placement(self.recording_schedule)
        assert self.course_page.visible_course_site_ids() == []

    def test_rescheduled_series_title_and_desc(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_rescheduled_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_rescheduled_series_publish_type(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)
        self.kaltura_page.verify_site_categories([self.site])

    # HISTORY

    def test_history_rec_placement(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.verify_history_row(field='publish_type',
                                            old_value=RecordingPlacement.PLACE_IN_MY_MEDIA.value['db'],
                                            new_value=RecordingPlacement.PUBLISH_AUTOMATICALLY.value['db'],
                                            requestor=self.old_instructor,
                                            status='succeeded',
                                            published=True)

    def test_history_rec_type(self):
        self.course_page.verify_history_row(field='recording_type',
                                            old_value=RecordingType.VIDEO_SANS_OPERATOR.value['db'],
                                            new_value=RecordingType.VIDEO_WITH_OPERATOR.value['db'],
                                            requestor=self.old_instructor,
                                            status='succeeded',
                                            published=True)

    def test_history_canvas_site(self):
        self.course_page.verify_history_row(field='canvas_site_ids',
                                            old_value=[],
                                            new_value=CoursePage.expected_site_ids_converter([self.site]),
                                            requestor=self.old_instructor,
                                            status='succeeded',
                                            published=True)

    def test_history_new_instructor(self):
        self.course_page.verify_history_row(field='instructor_uids',
                                            old_value=CoursePage.expected_uids_converter([self.old_instructor]),
                                            new_value=CoursePage.expected_uids_converter([self.new_instructor]),
                                            requestor=None,
                                            status='succeeded',
                                            published=True)
