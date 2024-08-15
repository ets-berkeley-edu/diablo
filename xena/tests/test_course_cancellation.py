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
from xena.pages.course_page import CoursePage
from xena.pages.ouija_board_page import OuijaBoardPage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCourseCancellation:

    # INITIALIZE TESTS

    test_data = util.get_test_script_course('test_course_cancellation')
    section = util.get_test_section(test_data)
    instructor = section.instructors[0]
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section, meeting)

    def test_setup(self):
        self.login_page.load_page()
        self.login_page.dev_auth()

        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

        self.jobs_page.click_blackouts_link()
        self.blackouts_page.create_all_blackouts()

        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.section)

        util.reset_section_test_data(self.section)

        util.reset_sent_email_test_data(self.section)

    # COURSE IS CANCELLED BEFORE SCHEDULING

    def test_cancel_pre_sched(self):
        util.delete_section(self.section)

    def test_cancel_pre_sched_no_search_result(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_cancel_pre_sched_no_admin_recording_opts(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_canceled()
        assert not self.course_page.is_present(CoursePage.COLLAB_EDIT_BUTTON)
        assert not self.course_page.is_present(CoursePage.RECORDING_TYPE_EDIT_BUTTON)
        assert not self.course_page.is_present(CoursePage.PLACEMENT_EDIT_BUTTON)

    def test_cancel_pre_sched_no_teacher_result(self):
        self.course_page.log_out()
        self.login_page.dev_auth(self.instructor.uid)
        self.courses_page.wait_for_title_contains('Eligible for Capture')
        assert not self.courses_page.is_present(OuijaBoardPage.course_row_link_locator(self.section))

    # SEMESTER START JOB SKIPS CANCELLED COURSE

    def test_cancel_pre_sched_jobs(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_cancel_pre_sched_no_kaltura_schedule_id(self):
        assert not util.get_kaltura_id(self.recording_schedule)

    def test_no_annunciation(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_ANNUNCIATION_SEM_START, self.section,
                                         self.instructor) == 0

    # COURSE IS RESTORED AND SCHEDULED

    def test_restored_pre_sched(self):
        util.restore_section(self.section)
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_kaltura_schedule_id(self):
        assert util.get_kaltura_id(self.recording_schedule)
        self.recording_schedule.recording_type = RecordingType.VIDEO_SANS_OPERATOR
        self.recording_schedule.recording_placement = RecordingPlacement.PUBLISH_TO_MY_MEDIA

    # COURSE CANCELED AGAIN

    def test_scheduled_canceled(self):
        util.delete_section(self.section)

    def test_course_page_canceled(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_canceled()

    # UNSCHEDULE CANCELED COURSE

    def test_unsched_canceled(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_no_kaltura_series_canceled_unsched(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_unsched_again_filter_all(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(self.section)
        self.ouija_page.filter_for_all()
        assert not self.ouija_page.is_course_in_results(self.section)

    def test_instructor_email_canceled_ineligible(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_COURSE_CANCELLED, self.section,
                                         self.instructor) == 1

    def test_history(self):
        self.course_page.load_page(self.section)
        self.course_page.verify_history_row(field='not_scheduled',
                                            old_value=None,
                                            new_value='—',
                                            requestor=None,
                                            status='succeeded',
                                            published=True)
