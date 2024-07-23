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
from xena.models.canvas_site import CanvasSite
from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeD:

    test_data = util.get_test_script_course('test_weird_type_d')
    section = util.get_test_section(test_data)
    meeting_0 = section.meetings[0]
    meeting_0.meeting_schedule.end_date = meeting_0.meeting_schedule.end_date - timedelta(days=8)
    meeting_1 = section.meetings[1]
    meeting_1.meeting_schedule.start_date = meeting_0.meeting_schedule.end_date + timedelta(days=1)
    recording_schedule_0 = RecordingSchedule(section, meeting_0)
    recording_schedule_1 = RecordingSchedule(section, meeting_1)

    site = CanvasSite(
        code=f'XENA Weird - {section.code}',
        name=f'XENA Weird - {section.code}',
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

    # CREATE COURSE SITE

    def test_create_course_site(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site)
        self.canvas_page.add_teacher_to_site(self.site, self.section, self.section.instructors[0])

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job_sequence()

        assert util.get_kaltura_id(self.recording_schedule_0)
        self.recording_schedule_0.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule_0.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

        assert util.get_kaltura_id(self.recording_schedule_1)
        self.recording_schedule_1.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule_1.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

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

    # VERIFY ANNUNCIATION EMAIL

    def test_receive_annunciation_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.section.instructors[0]) == 1

    # FIRST MEETING: VERIFY SERIES IN DIABLO

    def test_meeting_0_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_0.room)
        self.rooms_page.click_room_link(self.meeting_0.room)
        self.room_page.wait_for_series_row(self.recording_schedule_0)
        self.room_page.verify_series_link_text(self.recording_schedule_0)

    def test_meeting_0_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule_0)

    def test_meeting_0_room_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule_0)

    # SECOND MEETING: VERIFY SERIES IN DIABLO

    def test_meeting_1_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_1.room)
        self.rooms_page.click_room_link(self.meeting_1.room)
        self.room_page.wait_for_series_row(self.recording_schedule_1)
        self.room_page.verify_series_link_text(self.recording_schedule_1)

    def test_meeting_1_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule_1)

    def test_meeting_1_room_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule_1)

    # FIRST MEETING: VERIFY SERIES IN KALTURA

    def test_series_0_title_and_desc(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule_0)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)

    def test_series_0_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_0_publication(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule_0)

    def test_series_0_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)

    # SECOND MEETING: VERIFY SERIES IN KALTURA

    def test_series_1_title_and_desc(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_schedule_1)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)

    def test_series_1_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_1_publication(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule_1)

    def test_series_1_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)

    # VERIFY STATIC COURSE SIS DATA

    def test_course_page_link(self):
        self.kaltura_page.close_window_and_switch()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.section.instructors[0].uid)
        self.courses_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_visible_section_sis_data(self):
        self.course_page.verify_section_sis_data(self.section)

    def test_visible_meeting_0_sis_data(self):
        self.course_page.verify_meeting_sis_data(self.meeting_0, idx=0)

    def test_visible_meeting_1_sis_data(self):
        self.course_page.verify_meeting_sis_data(self.meeting_1, idx=1)

    # UPDATE SETTINGS, SAVE

    def test_choose_publish_type(self):
        self.course_page.click_edit_recording_placement()
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY, sites=[self.site])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule_0.recording_placement = RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY
        self.recording_schedule_1.recording_placement = RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY

    # UPDATE BOTH SERIES IN KALTURA

    def test_run_kaltura_job(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_meeting_0_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_0.series_id)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_schedule_0)
        assert len(self.kaltura_page.publish_category_els()) == 2
        assert self.kaltura_page.is_publish_category_present(self.site)

    def test_meeting_1_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_1.series_id)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_schedule_1)
        assert len(self.kaltura_page.publish_category_els()) == 2
        assert self.kaltura_page.is_publish_category_present(self.site)

    # VERIFY COURSE HISTORY

    def test_history_publish_type(self):
        self.course_page.load_page(self.section)
        old_val = RecordingPlacement.PUBLISH_TO_MY_MEDIA.value['db']
        new_val = RecordingPlacement.PUBLISH_TO_MEDIA_GALLERY.value['db']
        self.course_page.verify_history_row(field='publish_type',
                                            old_value=old_val,
                                            new_value=new_val,
                                            requestor=self.section.instructors[0],
                                            status='succeeded',
                                            published=True)

    def test_history_site_id(self):
        new_val = CoursePage.expected_site_ids_converter([self.site])
        self.course_page.verify_history_row(field='canvas_site_ids',
                                            old_value=[],
                                            new_value=new_val,
                                            requestor=self.section.instructors[0],
                                            status='succeeded',
                                            published=True)
