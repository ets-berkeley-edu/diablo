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
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestScheduling2:
    test_data = util.get_test_script_course('test_scheduling_2')
    section = util.get_test_section(test_data)
    instructor_0 = section.instructors[0]
    instructor_1 = section.instructors[1]
    meeting = section.meetings[0]
    meeting_schedule = meeting.meeting_schedule
    recording_schedule = RecordingSchedule(section, meeting)
    site_0 = CanvasSite(
        code=f'XENA Scheduling2.1 - {section.code}',
        name=f'XENA Scheduling2.1 - {section.code}',
        site_id=None,
    )
    site_1 = CanvasSite(
        code=f'XENA Scheduling2.2 - {section.code}',
        name=f'XENA Scheduling2.2 - {section.code}',
        site_id=None,
    )

    # DELETE PRE-EXISTING DATA

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

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        self.room_page.verify_series_link_text(self.recording_schedule)

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule)

    def test_room_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    # VERIFY SERIES IN KALTURA

    def test_series_title_and_desc(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting)

    def test_series_publish_status(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_kaltura_course_site(self):
        self.kaltura_page.verify_site_categories([])

    # VERIFY ANNUNCIATION EMAILS

    def test_receive_annunciation_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.instructor_1) == 1

    # CREATE COURSE SITE

    def test_create_course_site(self):
        self.kaltura_page.close_window_and_switch()
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site_0)
        self.canvas_page.add_teacher_to_site(self.site_0, self.section, self.instructor_0)
        self.canvas_page.add_teacher_to_site(self.site_0, self.section, self.instructor_1)

    # VERIFY STATIC COURSE SIS DATA

    def test_visible_section_sis_data(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_0.uid)
        self.instructor_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')
        self.course_page.verify_section_sis_data(self.section)

    def test_visible_meeting_sis_data(self):
        self.course_page.verify_meeting_sis_data(self.meeting, idx=0)

    def test_visible_listings(self):
        listing_codes = [li.code for li in self.section.listings]
        assert self.course_page.visible_cross_listing_codes() == listing_codes

    # VERIFY AVAILABLE OPTIONS

    def test_rec_type_options(self):
        assert not self.course_page.is_present(self.course_page.RECORDING_TYPE_EDIT_BUTTON)

    def test_rec_placement_options(self):
        self.course_page.click_edit_recording_placement()
        assert self.course_page.is_present(self.course_page.PLACEMENT_MY_MEDIA_RADIO)
        assert self.course_page.is_present(self.course_page.PLACEMENT_PENDING_RADIO)
        assert self.course_page.is_present(self.course_page.PLACEMENT_AUTOMATIC_RADIO)

    # SELECT OPTIONS, SAVE

    def test_choose_rec_placement(self):
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_AUTOMATICALLY, sites=[self.site_0])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_AUTOMATICALLY

    def test_visible_site_ids_updated(self):
        assert self.course_page.visible_course_site_ids() == [self.site_0.site_id]

    def test_site_link(self):
        assert self.course_page.external_link_valid(CoursePage.selected_placement_site_loc(self.site_0), self.site_0.name)

    def test_changes_queued(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_queued_changes_msg_present()

    # UPDATE SERIES IN KALTURA

    def test_update_run_kaltura_job(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    # VERIFY SERIES IN KALTURA

    def test_update_series_publish_status(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_update_kaltura_course_site(self):
        self.kaltura_page.verify_site_categories([self.site_0])

    # VERIFY EMAILS

    def test_update_receive_schedule_conf_email_instr_1(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor_0) == 1

    def test_update_receive_schedule_conf_email_instr_2(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor_1) == 1

    # CREATE COURSE SITE

    def test_create_another_course_site(self):
        self.kaltura_page.close_window_and_switch()
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site_1)
        self.canvas_page.add_teacher_to_site(self.site_1, self.section, self.instructor_0)
        self.canvas_page.add_teacher_to_site(self.site_1, self.section, self.instructor_1)

    def test_another_site_add_to_channels(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_1.uid)
        self.instructor_page.click_course_page_link(self.section)
        self.course_page.load_page(self.section)
        self.course_page.click_edit_recording_placement()
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_TO_PENDING, sites=[self.site_1])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_PENDING

    def test_another_site_visible_site_ids_updated(self):
        assert self.course_page.visible_course_site_ids() == [self.site_0.site_id, self.site_1.site_id]

    def test_another_site_link(self):
        assert self.course_page.external_link_valid(CoursePage.selected_placement_site_loc(self.site_1),
                                                    self.site_1.name)

    def test_changes_queued_again(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_queued_changes_msg_present()

    def test_another_site_run_kaltura_job(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    # VERIFY SERIES IN KALTURA

    def test_another_site_series_publish_status(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_another_site_kaltura_course_sites(self):
        self.kaltura_page.verify_site_categories([self.site_0, self.site_1])

    # VERIFY EMAILS

    def test_update_receive_site_conf_email_instr_1(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor_0) == 2

    def test_update_receive_site_conf_email_instr_2(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor_1) == 2

    # DELETE ONE COURSE SITE

    def test_delete_course_site(self):
        self.kaltura_page.close_window_and_switch()
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_1.uid)
        self.instructor_page.click_course_page_link(self.section)
        self.course_page.click_edit_recording_placement()
        self.course_page.remove_recording_placement_site(self.site_1)
        self.course_page.save_recording_placement_edits()

    def test_removed_site_visible_site_ids_updated(self):
        assert self.course_page.visible_course_site_ids() == [self.site_0.site_id]

    def test_changes_queued_removed_site(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_queued_changes_msg_present()

    def test_run_jobs(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.jobs_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_kaltura_removed_site_series_deleted(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_kaltura_new_series_course_site_deleted(self):
        assert util.get_kaltura_id(self.recording_schedule)
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.verify_site_categories([self.site_0])

    # INSTRUCTOR UPDATE PUBLISH TYPE

    def test_instructor_logs_in(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.course_page.hit_url(self.term.id, self.section.ccn)
        self.login_page.dev_auth(self.instructor_1.uid)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_update_publish_type(self):
        self.course_page.click_edit_recording_placement()
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_TO_MY_MEDIA.value)
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    def test_changes_queued_publish_type(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_queued_changes_msg_present()

    # UPDATE SERIES IN KALTURA

    def test_run_kaltura_job(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_deleted_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_new_kaltura_series(self):
        assert util.get_kaltura_id(self.recording_schedule)

    # VERIFY SERIES IN KALTURA

    def test_update_series_publish(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_publish_status(self.recording_schedule)
        self.kaltura_page.wait_for_publish_category_el()

    def test_updated_kaltura_no_course_site(self):
        self.kaltura_page.verify_site_categories([])

    # VERIFY EMAIL

    def test_updated_receive_schedule_conf_email_instr_1(self):
        self.kaltura_page.close_window_and_switch()
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor_0) == 3

    def test_updated_receive_schedule_conf_email_instr_2(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor_1) == 3

    # VERIFY COURSE HISTORY

    def test_history_pub_type_automatic(self):
        old_val = RecordingPlacement.PUBLISH_TO_MY_MEDIA.value['db']
        new_val = RecordingPlacement.PUBLISH_AUTOMATICALLY.value['db']
        self.course_page.verify_history_row('publish_type', old_val, new_val, self.instructor_0, 'succeeded',
                                            published=True)

    def test_history_add_site_0(self):
        old_val = '—'
        new_val = CoursePage.expected_site_ids_converter([self.site_0])
        self.course_page.verify_history_row('canvas_site_ids', old_val, new_val, self.instructor_0, 'succeeded',
                                            published=True)

    def test_history_add_site_1(self):
        old_val = CoursePage.expected_site_ids_converter([self.site_0])
        new_val = CoursePage.expected_site_ids_converter([self.site_0, self.site_1])
        self.course_page.verify_history_row('canvas_site_ids', old_val, new_val, self.instructor_1, 'succeeded',
                                            published=True)

    def test_history_pub_type_private(self):
        old_val = RecordingPlacement.PUBLISH_TO_PENDING.value['db']
        new_val = RecordingPlacement.PUBLISH_TO_MY_MEDIA.value['db']
        self.course_page.verify_history_row('publish_type', old_val, new_val, self.instructor_1, 'succeeded',
                                            published=True)

    def test_history_remove_site_1(self):
        old_val = CoursePage.expected_site_ids_converter([self.site_0, self.site_1])
        new_val = CoursePage.expected_site_ids_converter([self.site_0])
        self.course_page.verify_history_row('canvas_site_ids', old_val, new_val, self.instructor_1, 'succeeded',
                                            published=True)
