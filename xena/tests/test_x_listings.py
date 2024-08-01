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
from xena.models.user import User
from xena.pages.course_page import CoursePage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCrossListings:

    test_data = util.get_test_script_course('test_x_listings')
    admin = User({'uid': util.get_admin_uid()})
    sections = util.get_test_x_listed_sections(test_data)
    section = sections[0]
    instructor = section.instructors[0]
    x_listed_section = sections[1]
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section, meeting)
    site_1 = CanvasSite(
        code=f'XENA X-Listing - {section.code}',
        name=f'XENA X-Listing - {section.code}',
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
        self.kaltura_page.reset_test_data(self.x_listed_section)

        util.reset_section_test_data(self.section)
        util.delete_sis_sections_rows(self.x_listed_section)
        util.add_sis_sections_rows(self.x_listed_section)

        util.reset_sent_email_test_data(self.section)
        util.reset_sent_email_test_data(self.x_listed_section)

    # CREATE A COURSE SITE

    def test_create_course_site_one(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site_1)
        self.canvas_page.add_teacher_to_site(self.site_1, self.section, self.instructor)

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job_sequence()
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    def test_click_series_link(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_series_title(self):
        listing_codes = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        listing_codes.append(f'{self.section.code}, {self.section.number}')
        for code in listing_codes:
            assert code in self.kaltura_page.visible_series_title()

    def test_kaltura_publish_status(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_kaltura_course_site_count_two(self):
        self.kaltura_page.verify_site_categories([])

    def test_receive_annunciation_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.instructor) == 1

    def test_receive_annunciation_email_listing(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.x_listed_section,
                                         self.instructor) == 1

    # CHANGE PUBLISH TYPE TO AUTOMATIC

    def test_update_publish_type(self):
        self.course_page.load_page(self.section)
        self.course_page.click_edit_recording_placement()
        self.course_page.enter_recording_placement(RecordingPlacement.PUBLISH_AUTOMATICALLY, sites=[self.site_1])
        self.course_page.save_recording_placement_edits()
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_AUTOMATICALLY

    def test_update_run_kaltura_job(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_notify_of_changes_inst_1(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.instructor) == 1

    def test_listing_notify_of_changes_inst_1(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section.listings[0],
                                         self.instructor) == 1

    def test_update_click_series_link(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)

    def test_update_series_publish_status(self):
        self.kaltura_page.verify_publish_status(self.recording_schedule)

    def test_update_kaltura_course_site_count(self):
        self.kaltura_page.verify_site_categories([self.site_1])

    # CHANGE PRIMARY LISTING

    def test_switch_primary_kaltura_job(self):
        self.kaltura_page.close_window_and_switch()
        util.switch_principal_listing(self.section, self.x_listed_section)
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_switch_primary_series_title(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        listing_codes = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        listing_codes.append(f'{self.section.code}, {self.section.number}')
        for code in listing_codes:
            assert code in self.kaltura_page.visible_series_title()

    def test_switch_primary_site_count(self):
        self.kaltura_page.verify_site_categories([self.site_1])

    def test_switch_primary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # REVERT PRIMARY LISTING

    def test_revert_primary_kaltura_job(self):
        util.switch_principal_listing(self.x_listed_section, self.section)
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_revert_primary_series_title(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        listing_codes = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        listing_codes.append(f'{self.section.code}, {self.section.number}')
        for code in listing_codes:
            assert code in self.kaltura_page.visible_series_title()

    def test_revert_primary_site_count(self):
        self.kaltura_page.verify_site_categories([self.site_1])

    def test_revert_primary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # DELETE SECONDARY LISTING

    def test_not_canceled(self):
        util.delete_section(self.x_listed_section)
        self.course_page.load_page(self.section)
        assert not self.course_page.is_canceled()

    def test_no_x_listing(self):
        assert not self.course_page.visible_cross_listing_ccns()

    def test_delete_secondary_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_delete_secondary_site_count(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.verify_site_categories([self.site_1])

    def test_delete_secondary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # RESTORE SECONDARY LISTING

    def test_restored_secondary(self):
        util.restore_section(self.x_listed_section)
        self.course_page.load_page(self.section)
        expected = [f'{self.x_listed_section.code}, {self.x_listed_section.number}']
        visible = self.course_page.visible_cross_listing_codes()
        assert visible == expected

    def test_restored_secondary_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_restored_secondary_series_title(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        code = f'{self.x_listed_section.code}, {self.x_listed_section.number}'
        assert code in self.kaltura_page.visible_series_title()

    def test_restored_secondary_site_count(self):
        self.kaltura_page.verify_site_categories([self.site_1])

    def test_restored_secondary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # DELETE PRIMARY LISTING

    def test_canceled(self):
        util.delete_section(self.section)
        self.course_page.load_page(self.section)
        assert self.course_page.is_canceled()

    def test_x_listing(self):
        expected = [f'{self.x_listed_section.code}, {self.x_listed_section.number}']
        visible = self.course_page.visible_cross_listing_codes()
        assert visible == expected

    def test_canceled_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_series_deleted(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    # COURSE HISTORY

    def test_history_publish_type(self):
        self.course_page.load_page(self.section)
        old_val = RecordingPlacement.PUBLISH_TO_MY_MEDIA.value['db']
        new_val = RecordingPlacement.PUBLISH_AUTOMATICALLY.value['db']
        self.course_page.verify_history_row(field='publish_type',
                                            old_value=old_val,
                                            new_value=new_val,
                                            requestor=self.admin,
                                            status='succeeded',
                                            published=True)

    def test_history_canvas_site(self):
        new_val = CoursePage.expected_site_ids_converter([self.site_1])
        self.course_page.verify_history_row(field='canvas_site_ids',
                                            old_value='—',
                                            new_value=new_val,
                                            requestor=self.admin,
                                            status='succeeded',
                                            published=True)

    def test_history_secondary_section_deleted(self):
        self.course_page.verify_history_row(field='not_scheduled',
                                            old_value=None,
                                            new_value='—',
                                            requestor=None,
                                            status='succeeded',
                                            published=True)

    def test_history_primary_section_deleted(self):
        self.course_page.verify_history_row(field='not_scheduled',
                                            old_value=None,
                                            new_value='—',
                                            requestor=None,
                                            status='succeeded',
                                            published=True)
