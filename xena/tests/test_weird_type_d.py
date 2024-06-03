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

from flask import current_app as app
import pytest
from xena.models.canvas_site import CanvasSite
from xena.models.email_template_type import EmailTemplateType
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestWeirdTypeD:

    test_data = util.get_test_script_course('test_weird_type_d')
    section = util.get_test_section(test_data)
    meeting_0 = section.meetings[0]
    meeting_0.end_date = (meeting_0.end_date - timedelta(days=15)).strftime('%Y-%m-%d')
    meeting_1 = section.meetings[1]
    meeting_1.start_date = (meeting_0.end_date - timedelta(days=14)).strftime('%Y-%m-%d')
    recording_schedule_0 = RecordingSchedule(section, meeting_0)
    recording_schedule_1 = RecordingSchedule(section, meeting_1)

    site = CanvasSite(
        code=f'XENA Weird - {section.code}',
        name=f'XENA Weird - {section.code}',
        site_id=None,
    )

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_create_blackouts(self):
        self.jobs_page.click_blackouts_link()
        self.blackouts_page.delete_all_blackouts()
        self.blackouts_page.create_all_blackouts()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule_0)
        util.reset_section_test_data(self.section)

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.section)

    # CREATE COURSE SITE

    def test_create_course_site(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site)

    def test_enable_media_gallery(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MEDIA_GALLERY_TOOL']):
            self.canvas_page.load_site(self.site.site_id)
            self.canvas_page.enable_media_gallery(self.site)
            self.canvas_page.click_media_gallery_tool()
        else:
            app.logger.info('Media Gallery is not properly configured')
            raise

    def test_enable_my_media(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MY_MEDIA_TOOL']):
            self.canvas_page.load_site(self.site.site_id)
            self.canvas_page.enable_my_media(self.site)
            self.canvas_page.click_my_media_tool()
        else:
            app.logger.info('My Media is not properly configured')
            raise

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()
        assert util.get_kaltura_id(self.recording_schedule_0)
        self.recording_schedule_0.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule_0.publish_type = PublishType.PUBLISH_TO_MY_MEDIA
        assert util.get_kaltura_id(self.recording_schedule_1)
        self.recording_schedule_1.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule_1.publish_type = PublishType.PUBLISH_TO_MY_MEDIA

    def test_kaltura_blackouts(self):
        self.jobs_page.run_blackouts_job()

    # CHECK FILTERS - SCHEDULED

    def test_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_sched_status(self):
        visible_status = self.ouija_page.course_row_sched_status_el(self.section).text.strip()
        assert visible_status == self.recording_schedule_0.scheduling_status.value

    def test_scheduled_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # VERIFY COURSE HISTORY

    # TODO - admin view of just-scheduled course with 2 scheduled meetings

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

    def test_meeting_0_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule_0) == expected

    def test_meeting_0_room_series_start(self):
        start = self.meeting_0.meeting_schedule.expected_recording_dates(self.section.term)[0]
        assert self.room_page.series_row_start_date(self.recording_schedule_0) == start

    def test_meeting_0_room_series_end(self):
        last_date = self.meeting_0.meeting_schedule.expected_recording_dates(self.section.term)[-1]
        assert self.room_page.series_row_end_date(self.recording_schedule_0) == last_date

    def test_meeting_0_room_series_days(self):
        assert self.room_page.series_row_days(self.recording_schedule_0) == self.meeting_0.meeting_schedule.days.replace(' ', '')

    def test_meeting_0_series_recordings(self):
        self.room_page.expand_series_row(self.recording_schedule_0)
        expected = self.meeting_0.meeting_schedule.expected_recording_dates(self.section.term)
        visible = self.room_page.series_recording_start_dates(self.recording_schedule_0)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        expected.reverse()
        assert visible == expected

    def test_meeting_0_series_blackouts(self):
        expected = self.meeting_0.meeting_schedule.expected_blackout_dates(self.section.term)
        expected.sort()
        visible = self.room_page.series_recording_blackout_dates(self.recording_schedule_0)
        visible.sort()
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        assert visible == expected

    # SECOND MEETING: VERIFY SERIES IN DIABLO

    def test_meeting_1_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting_1.room)
        self.rooms_page.click_room_link(self.meeting_1.room)
        self.room_page.wait_for_series_row(self.recording_schedule_1)

    def test_meeting_1_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule_1) == expected

    def test_meeting_1_room_series_start(self):
        start = self.meeting_1.meeting_schedule.expected_recording_dates(self.section.term)[0]
        assert self.room_page.series_row_start_date(self.recording_schedule_1) == start

    def test_meeting_1_room_series_end(self):
        last_date = self.meeting_1.meeting_schedule.expected_recording_dates(self.section.term)[-1]
        assert self.room_page.series_row_end_date(self.recording_schedule_1) == last_date

    def test_meeting_1_room_series_days(self):
        assert self.room_page.series_row_days(self.recording_schedule_1) == self.meeting_1.meeting_schedule.days.replace(' ', '')

    def test_meeting_1_series_recordings(self):
        self.room_page.expand_series_row(self.recording_schedule_1)
        expected = self.meeting_1.meeting_schedule.expected_recording_dates(self.section.term)
        visible = self.room_page.series_recording_start_dates(self.recording_schedule_1)
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        expected.reverse()
        assert visible == expected

    def test_series_blackouts(self):
        expected = self.meeting_1.meeting_schedule.expected_blackout_dates(self.section.term)
        expected.sort()
        visible = self.room_page.series_recording_blackout_dates(self.recording_schedule_1)
        visible.sort()
        app.logger.info(f'Missing: {list(set(expected) - set(visible))}')
        app.logger.info(f'Unexpected: {list(set(visible) - set(expected))} ')
        assert visible == expected

    # FIRST MEETING: VERIFY SERIES IN KALTURA

    def test_click_series_0_link(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule_0)
        self.kaltura_page.wait_for_delete_button()

    def test_series_0_title_and_desc(self):
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)

    def test_series_0_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_0_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)

    def test_series_0_publication(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule_0)

    # SECOND MEETING: VERIFY SERIES IN KALTURA

    def test_click_series_1_link(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.click_kaltura_series_link(self.recording_schedule_1)
        self.kaltura_page.wait_for_delete_button()

    def test_series_1_title_and_desc(self):
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)

    def test_series_1_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_1_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)

    def test_series_1_publication(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule_1)

    # VERIFY STATIC COURSE SIS DATA

    def test_home_page(self):
        self.kaltura_page.close_window_and_switch()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_original.uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')

    def test_sign_up_link(self):
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_course_page_link(self):
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instructor_original.uid)
        self.ouija_page.wait_for_title_containing(f'Your {self.section.term.name} Course')
        self.ouija_page.click_course_page_link(self.section)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    def test_visible_ccn(self):
        assert self.course_page.visible_ccn() == self.section.ccn

    def test_visible_course_title(self):
        assert self.course_page.visible_course_title() == self.section.title

    def test_visible_instructors(self):
        instructor_names = [f'{self.instructor_original.first_name} {self.instructor_original.last_name}'.strip()]
        assert self.course_page.visible_instructors() == instructor_names

    def test_meeting_0_days(self):
        start = self.meeting_0.meeting_schedule.start_date
        end = self.meeting_0.meeting_schedule.end_date
        meeting_0_dates = f'{CoursePage.expected_term_date_str(start, end)}'
        assert meeting_0_dates in self.course_page.visible_meeting_days()[0]
        assert len(self.course_page.visible_meeting_days()) == 1

    def test_meeting_1_days(self):
        start = self.meeting_1.meeting_schedule.start_date
        end = self.meeting_1.meeting_schedule.end_date
        meeting_1_dates = f'{CoursePage.expected_term_date_str(start, end)}'
        assert meeting_1_dates in self.course_page.visible_meeting_days()[1]
        assert len(self.course_page.visible_meeting_days()) == 1

    def test_meeting_0_time(self):
        start = self.meeting_0.meeting_schedule.start_time
        end = self.meeting_0.meeting_schedule.end_time
        assert self.course_page.visible_meeting_time()[0] == f'{start} - {end}'

    def test_meeting_1_time(self):
        start = self.meeting_1.meeting_schedule.start_time
        end = self.meeting_1.meeting_schedule.end_time
        assert self.course_page.visible_meeting_time()[1] == f'{start} - {end}'
        assert len(self.course_page.visible_meeting_time()) == 2

    def test_meeting_0_room(self):
        assert self.course_page.visible_rooms()[0] == self.meeting_0.room.name
        assert len(self.course_page.visible_rooms()) == 1

    def test_meeting_1_room(self):
        assert self.course_page.visible_rooms()[1] == self.meeting_1.room.name
        assert len(self.course_page.visible_rooms()) == 2

    # UPDATE SETTINGS, SAVE

    def test_choose_publish_type(self):
        self.course_page.select_publish_type(PublishType.PUBLISH_AUTOMATICALLY)
        self.recording_schedule_0.publish_type = PublishType.PUBLISH_AUTOMATICALLY
        self.recording_schedule_1.publish_type = PublishType.PUBLISH_AUTOMATICALLY

    # TODO - enter Canvas site

    # TODO def test_confirmation(self):

    # UPDATE BOTH SERIES IN KALTURA

    def test_run_kaltura_job(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_meeting_0_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_0.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_0)
        self.kaltura_page.verify_publish_status(self.recording_schedule_0)
        assert len(self.kaltura_page.publish_category_els()) == 2
        assert self.kaltura_page.is_publish_category_present(self.site)

    def test_meeting_1_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_1.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section)
        self.kaltura_page.verify_schedule(self.section, self.meeting_1)
        self.kaltura_page.verify_publish_status(self.recording_schedule_1)
        assert len(self.kaltura_page.publish_category_els()) == 2
        assert self.kaltura_page.is_publish_category_present(self.site)

    # VERIFY COURSE HISTORY

    # TODO - admin view of updated course with 2 scheduled meetings
