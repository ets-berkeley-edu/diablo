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
import datetime

import pytest
from xena.models.canvas_site import CanvasSite
from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_placement import RecordingPlacement
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_type import RecordingType
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestScheduling0:
    test_data = util.get_test_script_course('test_scheduling_0')
    section = util.get_test_section(test_data)
    instructor = section.instructors[0]
    meeting = section.meetings[0]
    meeting_schedule = meeting.meeting_schedule
    recording_schedule = RecordingSchedule(section, meeting)
    site = CanvasSite(
        code=f'XENA Scheduling0 - {section.code}',
        name=f'XENA Scheduling0 - {section.code}',
        site_id=None,
    )

    # DELETE PRE-EXISTING DATA

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_emails_job()
        self.jobs_page.disable_all_jobs()

    def test_create_blackouts(self):
        self.jobs_page.click_blackouts_link()
        self.blackouts_page.delete_all_blackouts()
        self.blackouts_page.create_all_blackouts()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.recording_schedule)
        util.reset_section_test_data(self.section)

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.section)

    # CREATE COURSE SITE

    def test_create_course_site(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site)
        self.canvas_page.add_teacher_to_site(self.site, self.section, self.instructor)

    # CHECK FILTERS - NOT SCHEDULED

    def test_not_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_sched_status(self):
        assert self.ouija_page.visible_course_row_sched_status(self.section) == 'Not Scheduled'

    def test_not_scheduled_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # COURSE CAPTURE OPTIONS NOT AVAILABLE PRE-SCHEDULING

    def test_no_collaborator_edits(self):
        self.course_page.load_page(self.section)
        assert not self.course_page.is_present(CoursePage.COLLAB_EDIT_BUTTON)

    def test_no_recording_type_edits(self):
        assert not self.course_page.is_present(CoursePage.RECORDING_TYPE_EDIT_BUTTON)

    def test_no_recording_placement_edits(self):
        assert not self.course_page.is_present(CoursePage.PLACEMENT_EDIT_BUTTON)

    # VERIFY COURSE HISTORY

    def test_no_history(self):
        assert not self.course_page.update_history_table_rows()

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.publish_type = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    def test_kaltura_blackouts(self):
        self.jobs_page.run_blackouts_job()

    # CHECK FILTERS - SCHEDULED

    def test_scheduled_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_sched_status(self):
        assert self.ouija_page.visible_course_row_sched_status(self.section) == 'Scheduled'

    def test_scheduled_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_room_series_link(self):
        expected = f'{self.section.code}, {self.section.number} ({self.term.name})'
        assert self.room_page.series_row_kaltura_link_text(self.recording_schedule) == expected

    def test_room_series_schedule(self):
        self.room_page.verify_series_schedule(self.recording_schedule)

    def test_series_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_series_blackouts(self):
        self.room_page.verify_series_blackouts(self.recording_schedule)

    def test_verify_printable(self):
        self.room_printable_page.verify_printable(self.section, self.recording_schedule)

    # VERIFY SERIES IN KALTURA

    def test_click_series_link(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title_and_desc(self):
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_series_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting)

    def test_series_publish_status(self):
        assert self.kaltura_page.is_private()

    def test_kaltura_course_site(self):
        assert len(self.kaltura_page.publish_category_els()) == 0
        assert not self.kaltura_page.is_publish_category_present(self.site)

    # VERIFY ANNUNCIATION EMAIL

    def test_receive_annunciation_email(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.instructor) == 1

    # INSTRUCTOR LOGS IN

    def test_home_page(self):
        self.jobs_page.log_out()
        self.course_page.hit_url(self.term.id, self.section.ccn)
        self.login_page.dev_auth(self.instructor.uid)
        self.course_page.wait_for_diablo_title(f'{self.section.code}, {self.section.number}')

    # VERIFY STATIC COURSE SIS DATA

    def test_visible_ccn(self):
        assert self.course_page.visible_ccn() == self.section.ccn

    def test_visible_course_title(self):
        assert self.course_page.visible_course_title() == self.section.title

    def test_visible_instructors(self):
        assert self.course_page.visible_instructors() == [f'{self.instructor.first_name} {self.instructor.last_name}'.strip()]

    def test_visible_meeting_days(self):
        term_dates = f'{CoursePage.expected_term_date_str(self.meeting_schedule.start_date, self.meeting_schedule.end_date)}'
        assert term_dates in self.course_page.visible_meeting_days()[0]

    def test_visible_meeting_time(self):
        assert self.course_page.visible_meeting_time()[0] == f'{self.meeting_schedule.start_time} - {self.meeting_schedule.end_time}'

    def test_visible_room(self):
        assert self.course_page.visible_rooms()[0] == self.meeting.room.name

    def test_visible_site_ids(self):
        assert self.course_page.visible_course_site_ids() == []

    def test_visible_listings(self):
        listing_codes = [li.code for li in self.section.listings]
        assert self.course_page.visible_cross_listing_codes() == listing_codes

    # VERIFY DEFAULT SETTINGS AND EXTERNAL LINKS

    def test_default_instructors(self):
        assert self.course_page.visible_instructor_uids() == [str(self.instructor.uid)]

    def test_no_collaborators(self):
        assert not self.course_page.visible_collaborator_uids()

    def test_default_recording_type(self):
        assert self.course_page.visible_recording_type() == self.recording_schedule.recording_type.value['desc']

    def test_default_recording_placement(self):
        assert self.recording_schedule.publish_type.value['desc'] in self.course_page.visible_recording_placement()

    def test_no_instructor_kaltura_link(self):
        assert not self.course_page.is_present(self.course_page.kaltura_series_link(self.recording_schedule))

    # TODO - tests for variable links

    # VERIFY AVAILABLE OPTIONS

    def test_rec_type_options(self):
        self.course_page.click_rec_type_edit_button()
        assert self.course_page.is_present(self.course_page.RECORDING_TYPE_NO_OP_RADIO)
        assert self.course_page.is_present(self.course_page.RECORDING_TYPE_OP_RADIO)

    def test_rec_placement_options(self):
        self.course_page.cancel_recording_type_edits()
        self.course_page.click_edit_recording_placement()
        assert self.course_page.is_present(self.course_page.PLACEMENT_MY_MEDIA_RADIO)
        assert self.course_page.is_present(self.course_page.PLACEMENT_PENDING_RADIO)
        assert self.course_page.is_present(self.course_page.PLACEMENT_AUTOMATIC_RADIO)

    # SELECT OPTIONS, SAVE

    def test_choose_rec_type(self):
        self.course_page.cancel_recording_placement_edits()
        self.course_page.click_rec_type_edit_button()
        self.course_page.select_rec_type(RecordingType.VIDEO_WITH_OPERATOR)
        self.course_page.save_recording_type_edits()
        self.recording_schedule.recording_type = RecordingType.VIDEO_WITH_OPERATOR

    def test_rec_type_operator_no_going_back(self):
        assert not self.course_page.is_present(self.course_page.RECORDING_TYPE_EDIT_BUTTON)

    def test_choose_rec_placement(self):
        self.course_page.click_edit_recording_placement()
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_TO_PENDING, sites=[self.site])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.publish_type = RecordingPlacement.PUBLISH_TO_PENDING

    def test_visible_site_ids_updated(self):
        assert self.course_page.visible_course_site_ids() == [self.site.site_id]

    def test_site_link(self):
        assert self.course_page.external_link_valid(CoursePage.selected_placement_site_loc(self.site), self.site.name)

    # TODO - confirmation of changes message?

    def test_no_history_for_instructors(self):
        self.course_page.load_page(self.section)
        assert not self.course_page.update_history_table_rows()

    # VERIFY COURSE HISTORY

    def test_course_history_rec_type(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.course_page.load_page(self.section)
        row = next(filter(lambda r: r['field'] == 'recording_type', self.course_page.update_history_table_rows()))
        assert row['old_value'] == RecordingType.VIDEO_SANS_OPERATOR.value['db']
        assert row['new_value'] == RecordingType.VIDEO_WITH_OPERATOR.value['db']
        assert row['requested_by'] == str(self.instructor.uid)
        assert row['requested_at'] == datetime.date.today().strftime('%/%/%')
        assert row['status'] == 'queued'

    def test_course_history_rec_placement(self):
        row = next(filter(lambda r: r['field'] == 'publish_type', self.course_page.update_history_table_rows()))
        assert row['old_value'] == RecordingPlacement.PUBLISH_TO_MY_MEDIA.value['db']
        assert row['new_value'] == RecordingPlacement.PUBLISH_TO_PENDING.value['db']
        assert row['requested_by'] == str(self.instructor.uid)
        assert row['requested_at'] == datetime.date.today().strftime('%/%/%')
        assert row['status'] == 'queued'

    def test_course_history_canvas_site(self):
        row = next(filter(lambda r: r['field'] == 'canvas_site_id', self.course_page.update_history_table_rows()))
        assert row['old_value'] == '—'
        assert row['new_value'] == str(self.site.site_id)
        assert row['requested_by'] == str(self.instructor.uid)
        assert row['requested_at'] == datetime.date.today().strftime('%/%/%')
        assert row['status'] == 'queued'

    # UPDATE SERIES IN KALTURA

    def test_run_kaltura_job(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    # VERIFY SERIES IN DIABLO

    def test_update_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_update_open_printable(self):
        self.room_printable_page.verify_printable(self.section, self.recording_schedule)

    # VERIFY SERIES IN KALTURA

    def test_update_click_series_link(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_update_series_title_and_desc(self):
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_update_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_update_schedule(self):
        self.kaltura_page.verify_schedule(self.section, self.meeting)

    def test_update_series_publish_status(self):
        self.kaltura_page.reload_page()
        self.kaltura_page.wait_for_publish_category_el()
        # TODO - pending status
        assert self.kaltura_page.is_published()

    def test_update_kaltura_course_site(self):
        assert len(self.kaltura_page.publish_category_els()) == 2
        assert self.kaltura_page.is_publish_category_present(self.site)

    # VERIFY EMAILS

    def test_run_emails_job(self):
        self.kaltura_page.close_window_and_switch()
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()

    def test_update_receive_schedule_conf_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor) == 1

    def test_update_admin_email_operator_requested(self):
        assert util.get_sent_email_count(EmailTemplateType.ADMIN_OPERATOR_REQUESTED, self.section) == 1

    # VERIFY COURSE HISTORY

    def test_course_history_rec_type_updated(self):
        self.course_page.load_page(self.section)
        row = next(filter(lambda r: r['field'] == 'recording_type', self.course_page.update_history_table_rows()))
        assert row['status'] == 'succeeded'

    def test_course_history_rec_placement_updated(self):
        row = next(filter(lambda r: r['field'] == 'publish_type', self.course_page.update_history_table_rows()))
        assert row['status'] == 'succeeded'

    def test_course_history_canvas_site_updated(self):
        row = next(filter(lambda r: r['field'] == 'canvas_site_id', self.course_page.update_history_table_rows()))
        assert row['status'] == 'succeeded'

    # VERIFY REMINDER EMAIL

    # TODO
