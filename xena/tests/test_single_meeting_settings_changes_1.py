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
from xena.models.user import User
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestScheduling1:
    """
    SCENARIO.

    - Section has one instructor and one meeting
    - Admin opts the course in, recordings scheduled
    - Admin selects auto-publish, entering course site ID
    - Series updated
    """

    test_data = util.get_test_script_course('test_single_meeting_settings_changes_1')
    admin = User({'uid': util.get_admin_uid()})
    section = util.get_test_section(test_data)
    instructor = section.instructors[0]
    meeting = section.meetings[0]
    meeting_schedule = meeting.meeting_schedule
    recording_schedule = RecordingSchedule(section, meeting)
    site = CanvasSite(
        code=f'XENA Scheduling1 - {section.code}',
        name=f'XENA Scheduling1 - {section.code}',
        site_id=None,
    )

    # DELETE PRE-EXISTING DATA

    def test_setup(self):
        self.login_page.dev_auth()
        self.jobs_page.disable_all_jobs()
        self.blackouts_page.create_all_blackouts()
        self.kaltura_page.log_in_and_reset_test_data(self.calnet_page, [self.section])
        util.reset_section_and_user_test_data([self.section], [self.instructor])

    def test_new_class_eligible_email(self):
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=self.instructor) == 1

    # CHECK FILTERS - NOT SCHEDULED

    def test_not_scheduled_filter_all(self):
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_sched_status(self):
        assert self.ouija_page.visible_ouija_course_row_sched_status(self.section) == 'Not Scheduled'

    def test_not_scheduled_filter_eligible(self):
        self.ouija_page.filter_for_eligible()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_filter_eligible_unscheduled(self):
        self.ouija_page.filter_for_eligible_unscheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_filter_partially_approved(self):
        self.ouija_page.filter_for_partially_approved()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_not_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert not self.ouija_page.is_course_in_results(self.section)

    # VERIFY STATIC COURSE SIS DATA

    def test_visible_section_sis_data(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.load_page(self.section)
        self.course_page.verify_section_sis_data(self.section)

    def test_visible_meeting_sis_data(self):
        self.course_page.verify_meeting_sis_data(self.meeting, idx=0)

    def test_visible_site_ids(self):
        assert self.course_page.visible_course_site_ids() == []

    def test_visible_listings(self):
        listing_codes = [li.code for li in self.section.listings]
        assert self.course_page.visible_cross_listing_codes() == listing_codes

    # CREATE COURSE SITE

    def test_create_course_site(self):
        self.canvas_page.create_site(self.section, self.site, self.calnet_page)
        self.canvas_page.add_user_to_site(self.site, self.instructor, 'TA')

    # VERIFY AVAILABLE OPTIONS

    def test_admin_opt_in(self):
        self.instructor_page.load_admin_page(self.instructor)
        self.instructor_page.click_course_page_link(self.section)
        self.course_page.admin_opt_in_section(self.section)

    def test_opted_in_messaging(self):
        assert self.course_page.is_present(self.course_page.OPTED_IN_PENDING_MSG)

    def test_rec_placement_options(self):
        self.course_page.click_edit_recording_placement()
        assert self.course_page.is_present(self.course_page.PLACEMENT_MY_MEDIA_RADIO)
        assert self.course_page.is_present(self.course_page.PLACEMENT_AUTOMATIC_RADIO)

    def test_no_changes_to_rec_placement(self):
        self.course_page.select_recording_placement(RecordingPlacement.PUBLISH_AUTOMATICALLY)
        assert not self.course_page.element(self.course_page.PLACEMENT_SAVE_BUTTON).is_enabled()

    def test_add_new_site(self):
        self.course_page.enter_recording_placement(RecordingPlacement.PUBLISH_AUTOMATICALLY, sites=[self.site])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_AUTOMATICALLY

    def test_visible_site_ids_updated(self):
        assert self.course_page.visible_course_site_ids() == [self.site.site_id]

    # SCHEDULE RECORDINGS

    def test_update_job(self):
        self.jobs_page.run_schedule_update_and_kaltura_job_sequence()
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_AUTOMATICALLY

    # CHECK FILTERS - SCHEDULED

    def test_scheduled_filter_all(self):
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_sched_status(self):
        assert self.ouija_page.visible_ouija_course_row_sched_status(self.section) == 'Scheduled'

    def test_scheduled_filter_eligible(self):
        self.ouija_page.filter_for_eligible()
        assert self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_eligible_unscheduled(self):
        self.ouija_page.filter_for_eligible_unscheduled()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_no_instructors(self):
        self.ouija_page.filter_for_no_instructors()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_partially_approved(self):
        self.ouija_page.filter_for_partially_approved()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_scheduled_filter_scheduled(self):
        self.ouija_page.filter_for_scheduled()
        assert self.ouija_page.is_course_in_results(self.section)

    # VERIFY SERIES IN DIABLO

    def test_room_series(self):
        self.rooms_page.navigate_to_room_page(self.meeting.room)
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
        self.kaltura_page.verify_site_categories([self.site])

    # VERIFY EMAILS

    def test_class_eligible_email(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=self.instructor) == 1

    def test_class_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, self.section, self.instructor) == 1

    def test_settings_updated_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CHANGES_CONFIRMED, self.section, self.instructor) == 1

    # VERIFY COURSE HISTORY

    def test_course_history_row_count(self):
        self.kaltura_page.close_window_and_switch()
        self.course_page.load_page(self.section)
        assert self.course_page.update_history_row_count() == 4

    def test_course_total_sent_email(self):
        assert util.get_sent_email_count(template=None, section=None, instructor=self.instructor) == 3

    def test_course_history_instructor_added(self):
        self.course_page.verify_history_row(field='instructor_uids',
                                            old_value=[],
                                            new_value=CoursePage.expected_uids_converter([self.instructor]),
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_course_history_instructor_opt_in(self):
        self.course_page.verify_history_row(field='opted_in',
                                            old_value='—',
                                            new_value=f'{self.instructor.uid}',
                                            requestor=self.admin,
                                            status='succeeded',
                                            published=True)

    def test_course_history_publish_type_updated(self):
        self.course_page.verify_history_row(field='publish_type',
                                            old_value='—',
                                            new_value=RecordingPlacement.PUBLISH_AUTOMATICALLY.value['db'],
                                            requestor=self.admin,
                                            status='succeeded',
                                            published=True)

    def test_course_history_canvas_site_updated(self):
        self.course_page.verify_history_row(field='canvas_site_ids',
                                            old_value=[],
                                            new_value=CoursePage.expected_site_ids_converter([self.site]),
                                            requestor=self.admin,
                                            status='succeeded',
                                            published=True)

    def test_changes_no_longer_queued(self):
        assert not self.course_page.is_present(CoursePage.UPDATES_QUEUED_MSG)
