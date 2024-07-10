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
class TestCourseRoomChanges:

    section = util.get_test_section(util.get_test_script_course('test_course_changes_auditorium'))
    instr = section.instructors[0]
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section, meeting)

    new_ineligible_room = Section(util.get_test_script_course('test_course_changes_ineligible')).meetings[0].room
    new_eligible_room = Section(util.get_test_script_course('test_course_changes_eligible')).meetings[0].room

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

    # COURSE SCHEDULED, INSTRUCTOR SELECTS VIDEO OPERATOR

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job_sequence()
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR

    def test_welcome_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section, self.instr) == 1

    def test_modify_recording_settings(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.instr.uid)
        self.courses_page.click_course_page_link(self.section)
        self.course_page.click_rec_type_edit_button()
        self.course_page.select_rec_type(RecordingType.VIDEO_WITH_OPERATOR)
        self.course_page.save_recording_type_edits()
        self.recording_schedule.recording_type = RecordingType.VIDEO_WITH_OPERATOR

    def test_update_series(self):
        self.course_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_settings_update_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section, self.instr) == 1

    def test_paging_operator_email(self):
        assert util.get_sent_email_count(EmailTemplateType.ADMIN_OPERATOR_REQUESTED, self.section) == 1

    # SCHEDULED COURSE MOVES TO ANOTHER ELIGIBLE ROOM, THOUGH NOT AN AUDITORIUM

    def test_move_to_new_eligible_room(self):
        self.meeting.room = self.new_eligible_room
        util.set_meeting_location(self.section, self.meeting)

    def test_new_eligible_room_run_updates(self):
        self.jobs_page.run_schedule_update_job_sequence()
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR

    def test_new_eligible_room_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section, self.instr) == 1

    def test_settings_downgrade_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section, self.instr) == 2

    def test_new_eligible_room_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_new_eligible_room_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_new_eligible_room_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    def test_new_eligible_room_recording_type_downgrade(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.verify_recording_type(self.recording_schedule)
        self.course_page.verify_recording_placement(self.recording_schedule)

    def test_new_eligible_room_series_title_and_desc(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_new_eligible_room_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_new_eligible_room_publish_type(self):
        self.kaltura_page.verify_site_categories([])
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    # SCHEDULED COURSE MOVES TO INELIGIBLE ROOM

    def test_move_to_ineligible_room(self):
        self.kaltura_page.close_window_and_switch()
        util.change_course_room(self.section, self.meeting, self.new_ineligible_room)

    def test_update_jobs_ineligible_room(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_room_ineligible_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ROOM_CHANGE_INELIGIBLE, self.section, self.instr) == 1

    def test_ineligible_room_unschedule_series(self):
        assert not util.get_kaltura_id(self.recording_schedule)

    def test_no_ineligible_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_ineligible_room_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_ineligible_room_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_ineligible_room_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_ineligible_room_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # BACK TO ELIGIBLE ROOM, SETTINGS REVERT TO DEFAULT

    def test_move_back_to_eligible_room(self):
        util.change_course_room(self.section, self.meeting, self.new_eligible_room)

    def test_run_updated_jobs_eligible_room_again(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_eligible_room_again_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED, self.section, self.instr) == 1

    def test_eligible_room_again_reschedule_series(self):
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    def test_eligible_room_again_series(self):
        self.rooms_page.load_page()
        self.rooms_page.find_room(self.meeting.room)
        self.rooms_page.click_room_link(self.meeting.room)
        self.room_page.wait_for_series_row(self.recording_schedule)

    def test_eligible_room_again_recordings(self):
        self.room_page.verify_series_recordings(self.recording_schedule)

    def test_eligible_room_again_printable(self):
        self.room_printable_page.verify_printable(self.recording_schedule)

    def test_eligible_room_again_settings(self):
        self.room_printable_page.close_printable_schedule()
        self.course_page.load_page(self.section)
        self.course_page.verify_recording_type(self.recording_schedule)
        self.course_page.verify_recording_placement(self.recording_schedule)

    def test_eligible_room_again_series_title_and_desc(self):
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)

    def test_eligible_room_again_series_collab(self):
        self.kaltura_page.verify_collaborators(self.section)

    def test_eligible_room_again_publish_type(self):
        self.kaltura_page.verify_site_categories([])
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    # ROOM REMOVED ALTOGETHER

    def test_reset_data_null_test(self):
        self.kaltura_page.close_window_and_switch()
        util.change_course_room(self.section, self.meeting, new_room=None)

    def test_update_jobs_null_room(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_null_room_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ROOM_CHANGE_INELIGIBLE, self.section,
                                         self.instr) == 2

    def test_null_room_unschedule_series(self):
        assert not util.get_kaltura_id(self.recording_schedule)

    def test_no_null_room_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_null_room_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_null_room_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_null_room_filter_opted_out(self):
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_null_room_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    # VERIFY TOTAL EMAILS

    def test_welcome_email_ttl(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section, self.instr) == 1

    def test_settings_update_email_ttl(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section, self.instr) == 2

    def test_paging_operator_email_ttl(self):
        assert util.get_sent_email_count(EmailTemplateType.ADMIN_OPERATOR_REQUESTED, self.section) == 1

    def test_schedule_change_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_SCHEDULE_CHANGE, self.section, self.instr) == 1

    def test_room_ineligible_email_ttl(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ROOM_CHANGE_INELIGIBLE, self.section, self.instr) == 2

    def test_eligible_room_again_email_ttl(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_NEW_COURSE_SCHED, self.section, self.instr) == 1

    # HISTORY

    def test_history_rec_type_upgrade(self):
        old_val = RecordingType.VIDEO_SANS_OPERATOR.value['db']
        new_val = RecordingType.VIDEO_WITH_OPERATOR.value['db']
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row('recording_type', old_val, new_val, self.instr, 'succeeded', published=True)

    def test_history_rec_type_downgrade(self):
        old_val = RecordingType.VIDEO_WITH_OPERATOR.value['db']
        new_val = RecordingType.VIDEO_SANS_OPERATOR.value['db']
        self.course_page.verify_history_row('recording_type', old_val, new_val, None, 'succeeded', published=True)

    def test_history_new_eligible_room(self):
        old_val = None
        new_val = None
        self.course_page.verify_history_row('meeting_updated', old_val, new_val, None, 'succeeded', published=True)

    def test_history_no_room(self):
        old_val = None
        new_val = '—'
        self.course_page.verify_history_row('room_not_eligible', old_val, new_val, None, 'succeeded', published=True)
