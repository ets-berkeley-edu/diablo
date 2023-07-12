"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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
from xena.models.publish_type import PublishType
from xena.models.recording_approval_status import RecordingApprovalStatus
from xena.models.recording_schedule import RecordingSchedule
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.test_utils import util

"""
SCENARIO 0:
- Course has an instructor and a proxy
- Instructor signs up and grants proxy Kaltura perms
- Recordings scheduled
SCENARIO 1:
- Course has an instructor and no proxy
- Instructor signs up and grants proxy Kaltura perms
- Recordings scheduled
- One proxy is added in SIS data and added to Kaltura series
- Instructor wants proxy perms removed, so admin un-schedules and reschedules
SCENARIO 2:
- Course has an instructor and two proxies
- Instructor signs up and grants no proxy Kaltura perms
- Recordings scheduled
- Instructor wants proxy perms added, so admin un-schedules and reschedules
- One proxy with perms is removed from SIS data and not removed from Kaltura series
"""


@pytest.mark.usefixtures('page_objects')
class TestAPRX:

    scenario_0_test_data = util.get_test_script_course('test_aprx_0')
    scenario_0_section = util.get_test_section(scenario_0_test_data)
    scenario_0_meeting = scenario_0_section.meetings[0]
    recording_sched_0 = RecordingSchedule(scenario_0_section)

    scenario_1_test_data = util.get_test_script_course('test_aprx_1')
    scenario_1_section = util.get_test_section(scenario_1_test_data)
    scenario_1_meeting = scenario_1_section.meetings[0]
    recording_sched_1 = RecordingSchedule(scenario_1_section)

    scenario_2_test_data = util.get_test_script_course('test_aprx_2')
    scenario_2_section = util.get_test_section(scenario_2_test_data)
    scenario_2_meeting = scenario_2_section.meetings[0]
    recording_sched_2 = RecordingSchedule(scenario_2_section)

    def test_disable_jobs(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()

    def test_delete_old_kaltura(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.term, self.recording_sched_0)
        self.kaltura_page.reset_test_data(self.term, self.recording_sched_1)
        self.kaltura_page.reset_test_data(self.term, self.recording_sched_2)

    def test_delete_old_diablo(self):
        util.reset_sign_up_test_data(self.scenario_0_section)
        self.recording_sched_0.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_sched_0.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

        util.reset_sign_up_test_data(self.scenario_1_section)
        util.delete_course_instructor_row(self.scenario_1_section, self.scenario_1_section.proxies[0])
        self.recording_sched_1.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_sched_1.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

        util.reset_sign_up_test_data(self.scenario_2_section)
        self.recording_sched_2.approval_status = RecordingApprovalStatus.NOT_INVITED
        self.recording_sched_2.scheduling_status = RecordingSchedulingStatus.NOT_SCHEDULED

    def test_emails_pre_run(self):
        self.jobs_page.load_page()
        self.jobs_page.run_emails_job()

    def test_delete_old_email(self):
        util.reset_sent_email_test_data(self.scenario_0_section)
        util.reset_sent_email_test_data(self.scenario_1_section)
        util.reset_sent_email_test_data(self.scenario_2_section)

    # SCENARIO 0

    # Instructor signs up and grants proxy rights, recordings scheduled

    def test_scenario_0_sign_up_page(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.scenario_0_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.scenario_0_section)
        self.sign_up_page.select_publish_type(PublishType.KALTURA.value)
        self.sign_up_page.click_agree_checkbox()

    def test_scenario_0_visible_instructors(self):
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.scenario_0_section.instructors]
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_scenario_0_no_visible_proxies(self):
        proxy_names = [f'{p.first_name} {p.last_name}'.strip() for p in self.scenario_0_section.proxies]
        assert self.sign_up_page.visible_proxies() == proxy_names

    def test_scenario_0_aprx_perms_checked(self):
        self.sign_up_page.select_aprx_editor()

    def test_scenario_0_sign_up(self):
        self.sign_up_page.click_approve_button()
        self.sign_up_page.wait_for_approvals_msg('This course is currently queued for scheduling')

    def test_scenario_0_aprx_flag(self):
        assert self.sign_up_page.aprx_can_edit_flag() == 'Yes'

    def test_scenario_0_schedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched_0, self.term)

    def test_scenario_0_verify_series_title_and_desc(self):
        self.sign_up_page.load_page(self.scenario_0_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_0)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_0_section.code}, {self.scenario_0_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        course = f'{self.scenario_0_section.code}, {self.scenario_0_section.number} ({self.term.name})'
        instr = f'{self.scenario_0_section.instructors[0].first_name} {self.scenario_0_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_0_verify_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == 2

    def test_scenario_0_verify_series_instructor_rights(self):
        assert self.kaltura_page.collaborator_perm(self.scenario_0_section.instructors[0]) == 'Co-Editor, Co-Publisher'

    def test_scenario_0_re_verify_series_proxy_rights(self):
        assert self.kaltura_page.collaborator_perm(self.scenario_0_section.proxies[0]) == 'Co-Editor, Co-Publisher'

    def test_scenario_0_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    def test_scenario_0_changes_page(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.scenario_0_section)

    # SCENARIO 1

    # Instructor signs up and grants proxy rights

    def test_scenario_1_sign_up_page(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.scenario_1_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.scenario_1_section)
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()

    def test_scenario_1_visible_instructors(self):
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.scenario_1_section.instructors]
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_scenario_1_no_visible_proxies(self):
        assert self.sign_up_page.visible_proxies() == []

    def test_scenario_1_aprx_perms_selection_default(self):
        assert not self.sign_up_page.aprx_editor_checked()

    def test_scenario_1_aprx_perms_checked(self):
        self.sign_up_page.select_aprx_editor()

    def test_scenario_1_sign_up(self):
        self.sign_up_page.click_approve_button()
        self.sign_up_page.wait_for_approvals_msg('This course is currently queued for scheduling')

    def test_scenario_1_aprx_flag(self):
        assert self.sign_up_page.aprx_can_edit_flag() == 'Yes'

    def test_scenario_1_schedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched_1, self.term)

    def test_scenario_1_verify_series_title_and_desc(self):
        self.sign_up_page.load_page(self.scenario_1_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_1_section.code}, {self.scenario_1_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        course = f'{self.scenario_1_section.code}, {self.scenario_1_section.number} ({self.term.name})'
        instr = f'{self.scenario_1_section.instructors[0].first_name} {self.scenario_1_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_1_verify_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == 1

    def test_scenario_1_verify_series_instructor_rights(self):
        for instr in self.scenario_1_section.instructors:
            assert self.kaltura_page.collaborator_perm(instr) == 'Co-Editor, Co-Publisher'

    def test_scenario_1_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # Proxy added in SIS data and added to Kaltura series

    def test_scenario_1_add_proxy(self):
        util.delete_sis_sections_rows(self.scenario_1_section)
        util.add_sis_sections_rows(self.scenario_1_section)

    def test_scenario_1_rerun_kaltura(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_scenario_1_verify_series_title_and_desc_update(self):
        self.sign_up_page.load_page(self.scenario_1_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_1_section.code}, {self.scenario_1_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        course = f'{self.scenario_1_section.code}, {self.scenario_1_section.number} ({self.term.name})'
        instr = f'{self.scenario_1_section.instructors[0].first_name} {self.scenario_1_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_1_verify_series_collab_count_update(self):
        assert len(self.kaltura_page.collaborator_rows()) == 2

    def test_scenario_1_verify_series_instructor_rights_update(self):
        for instr in self.scenario_1_section.instructors:
            assert self.kaltura_page.collaborator_perm(instr) == 'Co-Editor, Co-Publisher'

    def test_scenario_1_verify_series_proxy_rights_update(self):
        for proxy in self.scenario_1_section.proxies:
            assert self.kaltura_page.collaborator_perm(proxy) == 'Co-Editor, Co-Publisher'

    def test_scenario_1_close_kaltura_window_again(self):
        self.kaltura_page.close_window_and_switch()

    def test_scenario_1_verify_proxy_on_sign_up(self):
        proxy_names = [f'{p.first_name} {p.last_name}' for p in self.scenario_1_section.proxies]
        assert self.sign_up_page.visible_proxies() == proxy_names

    def test_scenario_1_no_proxy_on_changes(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.scenario_1_section)

    # Admin reschedules to revoke proxy perms

    def test_scenario_1_unschedule(self):
        self.sign_up_page.load_page(self.scenario_1_section)
        self.sign_up_page.confirm_unscheduling(self.recording_sched_1)
        assert not util.get_kaltura_id(self.recording_sched_1, self.term)

    def test_scenario_1_deselect_proxy_rights(self):
        self.sign_up_page.deselect_aprx_editor()

    def test_scenario_1_re_approve(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_approve_button()
        self.sign_up_page.wait_for_approvals_msg('This course is currently queued for scheduling')

    def test_scenario_1_aprx_flag_revoked(self):
        assert self.sign_up_page.aprx_can_edit_flag() == 'No'

    def test_scenario_1_reschedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched_1, self.term)

    def test_scenario_1_re_verify_series_title_and_desc(self):
        self.sign_up_page.load_page(self.scenario_1_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_1)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_1_section.code}, {self.scenario_1_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        instr = f'{self.scenario_1_section.instructors[0].first_name} {self.scenario_1_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_1_re_verify_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == 1

    def test_scenario_1_re_verify_series_instructor_rights(self):
        for instr in self.scenario_1_section.instructors:
            assert self.kaltura_page.collaborator_perm(instr) == 'Co-Editor, Co-Publisher'

    def test_scenario_1_re_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    def test_scenario_1_changes_page(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.scenario_1_section)

    # SCENARIO 2

    # Instructor signs up and grants no rights to proxies

    def test_scenario_2_sign_up_page(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(self.scenario_2_section.instructors[0].uid)
        self.ouija_page.click_sign_up_page_link(self.scenario_2_section)

    def test_scenario_2_visible_instructors(self):
        self.sign_up_page.wait_for_diablo_title(f'{self.scenario_2_section.code}, {self.scenario_2_section.number}')
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.scenario_2_section.instructors]
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_scenario_2_visible_proxies(self):
        proxy_names = [f'{p.first_name} {p.last_name}'.strip() for p in self.scenario_2_section.proxies]
        assert self.sign_up_page.visible_proxies() == proxy_names

    def test_scenario_2_aprx_perms_selection_default(self):
        assert not self.sign_up_page.aprx_editor_checked()

    def test_scenario_2_sign_up(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_agree_checkbox()
        self.sign_up_page.click_approve_button()
        self.sign_up_page.wait_for_approvals_msg('This course is currently queued for scheduling')

    def test_scenario_2_aprx_flag(self):
        assert self.sign_up_page.aprx_can_edit_flag() == 'No'

    def test_scenario_2_schedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched_2, self.term)

    def test_scenario_2_verify_series_title_and_desc(self):
        self.sign_up_page.load_page(self.scenario_2_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_2)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_2_section.code}, {self.scenario_2_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        instr = f'{self.scenario_2_section.instructors[0].first_name} {self.scenario_2_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_2_verify_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == 1

    def test_scenario_2_verify_series_instructor_rights(self):
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.instructors[0]) == 'Co-Editor, Co-Publisher'

    def test_scenario_2_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # Admin reschedules to grant proxy perms

    def test_scenario_2_unschedule(self):
        self.sign_up_page.load_page(self.scenario_2_section)
        self.sign_up_page.confirm_unscheduling(self.recording_sched_2)
        assert not util.get_kaltura_id(self.recording_sched_2, self.term)

    def test_scenario_2_reschedule_sign_up_page(self):
        self.sign_up_page.load_page(self.scenario_2_section)

    def test_scenario_2_reschedule_visible_instructors(self):
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.scenario_2_section.instructors]
        assert self.sign_up_page.visible_instructors() == instructor_names

    def test_scenario_2_reschedule_visible_proxies(self):
        proxy_names = [f'{p.first_name} {p.last_name}'.strip() for p in self.scenario_2_section.proxies]
        assert self.sign_up_page.visible_proxies() == proxy_names

    def test_scenario_2_select_proxy_rights(self):
        self.sign_up_page.select_aprx_editor()

    def test_scenario_2_re_approve(self):
        self.sign_up_page.select_publish_type(PublishType.BCOURSES.value)
        self.sign_up_page.click_approve_button()
        self.sign_up_page.wait_for_approvals_msg('This course is currently queued for scheduling')

    def test_scenario_2_aprx_flag_granted(self):
        assert self.sign_up_page.aprx_can_edit_flag() == 'Yes'

    def test_scenario_2_reschedule_recordings(self):
        self.sign_up_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_sched_2, self.term)

    def test_scenario_2_re_verify_series_title_and_desc(self):
        self.sign_up_page.load_page(self.scenario_2_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_2)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_2_section.code}, {self.scenario_2_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        instr = f'{self.scenario_2_section.instructors[0].first_name} {self.scenario_2_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_2_re_verify_series_collab_count(self):
        assert len(self.kaltura_page.collaborator_rows()) == 3

    def test_scenario_2_re_verify_series_instructor_rights(self):
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.instructors[0]) == 'Co-Editor, Co-Publisher'

    def test_scenario_2_re_verify_series_proxy_rights(self):
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.proxies[0]) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.proxies[1]) == 'Co-Editor, Co-Publisher'

    def test_scenario_2_re_close_kaltura_window(self):
        self.kaltura_page.close_window_and_switch()

    # Proxy removed by SIS, not removed from Kaltura

    def test_scenario_2_proxy_removed(self):
        util.delete_course_instructor_row(self.scenario_2_section, self.scenario_2_section.proxies[1])

    def test_scenario_2_verify_sign_up_no_proxy(self):
        self.sign_up_page.load_page(self.scenario_2_section)
        instructor_names = [f'{i.first_name} {i.last_name}'.strip() for i in self.scenario_2_section.instructors]
        assert self.sign_up_page.visible_instructors() == instructor_names
        proxy_names = [f'{self.scenario_2_section.proxies[0].first_name} {self.scenario_2_section.proxies[0].last_name}'.strip()]
        assert self.sign_up_page.visible_proxies() == proxy_names

    def test_scenario_2_run_kaltura_job(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_scenario_2_changes_page(self):
        self.changes_page.load_page()
        self.changes_page.wait_for_results()
        assert not self.changes_page.is_course_row_present(self.scenario_2_section)

    def test_scenario_2_verify_kaltura_series(self):
        self.sign_up_page.load_page(self.scenario_2_section)
        self.sign_up_page.click_kaltura_series_link(self.recording_sched_2)
        self.kaltura_page.wait_for_delete_button()
        course = f'{self.scenario_2_section.code}, {self.scenario_2_section.number} ({self.term.name})'
        assert self.kaltura_page.visible_series_title() == course
        instr = f'{self.scenario_2_section.instructors[0].first_name} {self.scenario_2_section.instructors[0].last_name}'.strip()
        expected_desc = f'{course} is taught by {instr}.'
        assert expected_desc in self.kaltura_page.visible_series_desc()

    def test_scenario_2_verify_proxy_removed(self):
        assert len(self.kaltura_page.collaborator_rows()) == 3

    def test_scenario_2_verify_instructor_not_removed(self):
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.instructors[0]) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.proxies[0]) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.scenario_2_section.proxies[1]) == 'Co-Editor, Co-Publisher'
