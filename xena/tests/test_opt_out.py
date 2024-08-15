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
from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_schedule import RecordingSchedule
from xena.test_utils import util

sections = util.get_test_opt_out_sections()

section_0 = sections[0]
meeting_0_0 = section_0.meetings[0].meeting_schedule
meeting_0_1 = section_0.meetings[1].meeting_schedule
meeting_0_0.end_date = meeting_0_0.end_date - timedelta(days=8)
meeting_0_1.start_date = meeting_0_0.end_date + timedelta(days=1)

section_1 = sections[1]

instructor_0 = section_1.instructors[0]
instructor_1 = next(filter(lambda inst: inst.uid != instructor_0.uid, section_0.instructors))

recording_schedule_0_0 = RecordingSchedule(section_0, section_0.meetings[0])
recording_schedule_0_1 = RecordingSchedule(section_0, section_0.meetings[1])
recording_schedule_1 = RecordingSchedule(section_1, section_1.meetings[0])


@pytest.mark.usefixtures('page_objects')
class TestOptOut0:

    # Instructor opted out of previous term.
    # Recordings scheduled for current term.
    # Instructor opts out of all terms.
    # Recordings unscheduled.

    def test_set_up(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

        self.jobs_page.run_emails_job()
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section_1)

        self.jobs_page.click_blackouts_link()
        self.blackouts_page.delete_all_blackouts()

        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.reset_section_test_data(section_1)

    def test_opt_out_prev_term(self):
        util.set_past_term_opt_out(instructor_0)

    def test_semester_start_up(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()

    def test_both_sections_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0_0)
        assert util.get_kaltura_id(recording_schedule_0_1)
        assert util.get_kaltura_id(recording_schedule_1)

    def test_section_0_not_opted_out(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(section_0)
        self.ouija_page.filter_for_opted_out()
        assert not self.ouija_page.is_course_in_results(section_0)

    def test_section_1_not_opted_out(self):
        self.ouija_page.search_for_course_code(section_1)
        assert not self.ouija_page.is_course_in_results(section_1)

    def test_opt_out_all_terms(self):
        self.ouija_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.enable_opt_out_all_terms()

    def test_run_update(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_both_sections_unscheduled(self):
        self.kaltura_page.load_event_edit_page(recording_schedule_0_0.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_0_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_section_0_opted_out(self):
        self.ouija_page.load_page()
        self.ouija_page.search_for_course_code(section_0)
        self.ouija_page.filter_for_opted_out()
        assert self.ouija_page.is_course_in_results(section_0)

    def test_section_1_opted_out(self):
        self.ouija_page.search_for_course_code(section_1)
        assert self.ouija_page.is_course_in_results(section_1)

    def test_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptOut1:

    # Instructor is opted out of all terms.
    # Recordings in the current term are not scheduled.
    # Instructor opts in all terms.
    # Recordings are scheduled.

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_0, delete_opt_outs=False)
        util.reset_section_test_data(section_1, delete_opt_outs=False)

    def test_semester_start_up(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()
        self.jobs_page.run_emails_job()

    def test_no_sections_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_0_0)
        assert not util.get_kaltura_id(recording_schedule_0_1)
        assert not util.get_kaltura_id(recording_schedule_1)

    def test_no_opt_out_emails(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 0
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 0
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 0

    def test_opt_in_all_terms(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.disable_opt_out_all_terms()

    def test_run_update(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_both_sections_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0_0)
        assert util.get_kaltura_id(recording_schedule_0_1)
        assert util.get_kaltura_id(recording_schedule_1)


@pytest.mark.usefixtures('page_objects')
class TestOptOut2:

    # Instructor has no opt-outs
    # Recordings are scheduled
    # Instructor opts out of one section
    # That section's recordings unscheduled

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.reset_section_test_data(section_1)

    def test_semester_start_up(self):
        self.jobs_page.load_page()
        self.jobs_page.run_semester_start_job()

    def test_both_sections_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0_0)
        assert util.get_kaltura_id(recording_schedule_0_1)
        assert util.get_kaltura_id(recording_schedule_1)

    def test_opt_out_one_section(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_1.uid)
        self.instructor_page.enable_opt_out_section(section_0)

    def test_run_update(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_one_sections_unscheduled(self):
        self.kaltura_page.load_event_edit_page(recording_schedule_0_0.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_0_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_1.series_id)
        self.kaltura_page.wait_for_delete_button()

    def test_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 0
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_1) == 0


@pytest.mark.usefixtures('page_objects')
class TestOptOut3:

    # Instructor has opted out of a previous term
    # Recordings scheduled in the current term
    # Instructor opts out of current term also
    # All instructor sections unscheduled

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.reset_section_test_data(section_1)

    def test_opt_out_prev_term(self):
        util.set_past_term_opt_out(instructor_1)

    def test_run_update(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_both_sections_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0_0)
        assert util.get_kaltura_id(recording_schedule_0_1)
        assert util.get_kaltura_id(recording_schedule_1)

    def test_opt_out_current_term(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.enable_opt_out_current_term()

    def test_run_update_encore(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_both_sections_unscheduled(self):
        self.kaltura_page.load_event_edit_page(recording_schedule_0_0.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_0_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptOut4:

    # Instructor is opted out of all terms
    # Recordings not scheduled
    # Instructor opts in to one section
    # Recordings scheduled for that section only

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.reset_section_test_data(section_1)

    def test_opt_out_all_terms(self):
        self.jobs_page.load_page()
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.enable_opt_out_all_terms()

    def test_run_update(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_no_sections_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_0_0)
        assert not util.get_kaltura_id(recording_schedule_0_1)
        assert not util.get_kaltura_id(recording_schedule_1)

    def test_no_opt_out_emails(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 0
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 0
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 0

    def test_opt_in_one_section(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.disable_opt_out_all_terms()
        self.instructor_page.enable_opt_out_section(section_0)

    def test_run_update_encore(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_one_section_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_0_0)
        assert not util.get_kaltura_id(recording_schedule_0_1)
        assert util.get_kaltura_id(recording_schedule_1)

    def test_no_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 0


@pytest.mark.usefixtures('page_objects')
class TestOptOut5:

    # Instructor is not opted out
    # Recordings scheduled
    # Instructor opts out of all terms
    # Recordings unscheduled for all sections

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.reset_section_test_data(section_1)

    def test_run_update(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_both_sections_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0_0)
        assert util.get_kaltura_id(recording_schedule_0_1)
        assert util.get_kaltura_id(recording_schedule_1)

    def test_opt_out_all_terms(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.enable_opt_out_all_terms()

    def test_run_update_encore(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_both_sections_unscheduled(self):
        self.kaltura_page.load_event_edit_page(recording_schedule_0_0.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_0_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')
        self.kaltura_page.load_event_edit_page(recording_schedule_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_0, instructor_1) == 1
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptOut6:

    # A section has no instructor
    # Recordings are scheduled
    # An instructor who has opted out of all terms is added to the section
    # Recordings are unscheduled

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_1)

        util.change_course_instructor(section_1, old_instructor=instructor_0, new_instructor=None)

    def test_run_update(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_section_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1)

    def test_opt_out_all_terms(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(instructor_0.uid)
        self.instructor_page.enable_opt_out_all_terms()

    def test_add_instructors_to_sections(self):
        util.change_course_instructor(section_1, old_instructor=None, new_instructor=instructor_0)

    def test_run_update_encore(self):
        self.instructor_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_section_unscheduled(self):
        self.kaltura_page.load_event_edit_page(recording_schedule_1.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_no_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptOut7:

    # A section has an instructor opted out of all terms
    # Recordings are not scheduled
    # The instructor is removed
    # Recordings are scheduled

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)

        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_1, delete_opt_outs=False)

    def test_run_update(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_section_not_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1)

    def test_remove_obstructive_instructor(self):
        util.change_course_instructor(section_1, old_instructor=instructor_0, new_instructor=None)

    def test_run_update_encore(self):
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()
        self.jobs_page.run_emails_job()

    def test_section_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1)

    def test_no_opt_out_emails_sent(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTR_OPTED_OUT, section_1, instructor_0) == 0
