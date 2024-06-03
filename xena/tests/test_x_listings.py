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

from flask import current_app as app
import pytest
from xena.models.canvas_site import CanvasSite
from xena.models.email_template_type import EmailTemplateType
from xena.models.publish_type import PublishType
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.recording_type import RecordingType
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCrossListings:

    test_data = util.get_test_script_course('test_x_listings')
    sections = util.get_test_x_listed_sections(test_data)
    section = sections[0]
    x_listed_section = sections[1]
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section)
    site_1 = CanvasSite(
        code=f'XENA X-Listing One - {section.code}',
        name=f'XENA X-Listing One - {section.code}',
        site_id=None,
    )
    site_2 = CanvasSite(
        code=f'XENA X-Listing Two - {x_listed_section.code}',
        name=f'XENA X-Listing Two - {x_listed_section.code}',
        site_id=None,
    )

    # DELETE PRE-EXISTING DATA

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_emails_job()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_diablo_and_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_schedule)

    # TODO - delete old course sites?

    def test_delete_old_diablo_data(self):
        util.reset_section_test_data(self.section)
        util.delete_sis_sections_rows(self.x_listed_section)
        util.add_sis_sections_rows(self.x_listed_section)
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.section)
        util.reset_sent_email_test_data(self.x_listed_section)

    # CREATE A COURSE SITE FOR EACH OF THE LISTINGS

    def test_create_course_site_one(self):
        self.canvas_page.provision_site(self.section, [self.section.ccn], self.site_1)

    def test_enable_media_gallery_1(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MEDIA_GALLERY_TOOL']):
            self.canvas_page.load_site(self.site_1.site_id)
            self.canvas_page.enable_media_gallery(self.site_1)
            self.canvas_page.click_media_gallery_tool()
        else:
            app.logger.info('Media Gallery is not properly configured')
            raise

    def test_enable_my_media_1(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MY_MEDIA_TOOL']):
            self.canvas_page.load_site(self.site_1.site_id)
            self.canvas_page.enable_my_media(self.site_1)
            self.canvas_page.click_my_media_tool()
        else:
            app.logger.info('My Media is not properly configured')
            raise

    def test_create_course_site_two(self):
        self.canvas_page.provision_site(self.x_listed_section, [self.x_listed_section.ccn], self.site_2)

    def test_enable_media_gallery_2(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MEDIA_GALLERY_TOOL']):
            self.canvas_page.load_site(self.site_2.site_id)
            self.canvas_page.enable_media_gallery(self.site_2)
            self.canvas_page.click_media_gallery_tool()
        else:
            app.logger.info('Media Gallery is not properly configured')
            raise

    def test_enable_my_media_2(self):
        if self.canvas_page.is_tool_configured(app.config['CANVAS_MY_MEDIA_TOOL']):
            self.canvas_page.load_site(self.site_2.site_id)
            self.canvas_page.enable_my_media(self.site_2)
            self.canvas_page.click_my_media_tool()
        else:
            app.logger.info('My Media is not properly configured')
            raise

    # RUN SEMESTER START JOB

    def test_semester_start(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()
        self.jobs_page.run_emails_job()

    def test_kaltura_schedule_id(self):
        util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.publish_type = PublishType.PUBLISH_TO_MY_MEDIA
        self.recording_schedule.scheduling_status = RecordingSchedulingStatus.SCHEDULED

    def test_kaltura_blackouts(self):
        self.jobs_page.run_blackouts_job()

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
        self.kaltura_page.wait_for_publish_category_el()
        assert self.kaltura_page.is_private()

    def test_kaltura_course_site_count_two(self):
        assert not len(self.kaltura_page.publish_category_els())

    def test_kaltura_course_sites(self):
        assert not self.kaltura_page.is_publish_category_present(self.site_1)
        assert not self.kaltura_page.is_publish_category_present(self.site_2)

    def test_receive_annunciation_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.section.instructors[0]) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.section.instructors[1]) == 1

    # CHANGE PUBLISH TYPE TO AUTOMATIC

    def test_update_publish_type(self):
        self.course_page.load_page(self.section)
        self.course_page.select_publish_type(PublishType.PUBLISH_AUTOMATICALLY.value)
        # TODO - select both sites
        self.recording_schedule.publish_type = PublishType.PUBLISH_AUTOMATICALLY

    def test_approve(self):
        self.course_page.click_approve_button()

    # TODO def test_course_history_updates_pending(self):

    def test_update_run_kaltura_job(self):
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_notify_of_changes_inst_1(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.section.instructors[0]) == 1

    def test_notify_of_changes_inst_2(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section,
                                         self.section.instructors[1]) == 1

    def test_listing_notify_of_changes_inst_1(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_CHANGES_CONFIRMED, self.section.listings[0],
                                         self.section.instructors[0]) == 1

    def test_update_click_series_link(self):
        self.course_page.load_page(self.section)
        self.course_page.click_kaltura_series_link(self.recording_schedule)
        self.kaltura_page.wait_for_delete_button()

    def test_update_series_publish_status(self):
        assert self.kaltura_page.is_published()

    def test_update_kaltura_course_site_count(self):
        assert len(self.kaltura_page.publish_category_els()) == 4

    def test_update_kaltura_course_site(self):
        assert self.kaltura_page.is_publish_category_present(self.site_1)
        assert self.kaltura_page.is_publish_category_present(self.site_2)

    def test_update_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # CHANGE PRIMARY LISTING

    def test_switch_primary_listing(self):
        util.switch_principal_listing(self.section, self.x_listed_section)

    def test_switch_primary_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_switch_primary_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)

    def test_switch_primary_series_title(self):
        listing_codes = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        listing_codes.append(f'{self.section.code}, {self.section.number}')
        for code in listing_codes:
            assert code in self.kaltura_page.visible_series_title()

    def test_switch_primary_site_count(self):
        assert len(self.kaltura_page.publish_category_els()) == 4

    def test_switch_primary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # TODO course history

    # REVERT PRIMARY LISTING

    def test_revert_primary_listing(self):
        util.switch_principal_listing(self.x_listed_section, self.section)

    def test_revert_primary_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_revert_primary_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)

    def test_revert_primary_series_title(self):
        listing_codes = [f'{listing.code}, {self.section.number}' for listing in self.section.listings]
        listing_codes.append(f'{self.section.code}, {self.section.number}')
        for code in listing_codes:
            assert code in self.kaltura_page.visible_series_title()

    def test_revert_primary_site_count(self):
        assert len(self.kaltura_page.publish_category_els()) == 4

    def test_revert_primary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # TODO course history

    # DELETE SECONDARY LISTING

    def test_delete_secondary_listing(self):
        util.delete_section(self.x_listed_section)

    def test_not_canceled(self):
        self.course_page.load_page(self.section)
        assert not self.course_page.is_canceled()

    def test_no_x_listing(self):
        assert not self.course_page.visible_cross_listing_ccns()

    def test_delete_secondary_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_delete_secondary_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)

    def test_delete_secondary_series_title(self):
        code = f'{self.x_listed_section.code}, {self.x_listed_section.number}'
        assert code not in self.kaltura_page.visible_series_title()

    def test_delete_secondary_site_count(self):
        assert len(self.kaltura_page.publish_category_els()) == 2

    def test_delete_secondary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # TODO course history

    # RESTORE SECONDARY LISTING

    def test_restore_secondary(self):
        util.restore_section(self.x_listed_section)

    def test_restored_secondary(self):
        self.course_page.load_page(self.section)
        expected = [f'{self.x_listed_section.code}, {self.x_listed_section.number}']
        visible = self.course_page.visible_cross_listing_codes()
        assert visible == expected

    def test_restored_secondary_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_restored_secondary_kaltura_series(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)

    def test_restored_secondary_series_title(self):
        code = f'{self.x_listed_section.code}, {self.x_listed_section.number}'
        assert code in self.kaltura_page.visible_series_title()

    def test_restored_secondary_site_count(self):
        assert len(self.kaltura_page.publish_category_els()) == 4

    def test_restored_secondary_collaborators(self):
        self.kaltura_page.verify_collaborators(self.section)

    # TODO course history

    # DELETE PRIMARY LISTING

    def test_delete_primary_listing(self):
        util.delete_section(self.section)

    def test_canceled(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_canceled()

    def test_x_listing(self):
        expected = [f'{self.x_listed_section.code}, {self.x_listed_section.number}']
        visible = self.course_page.visible_cross_listing_codes()
        assert visible == expected

    def test_series_deleted(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    # TODO course history
