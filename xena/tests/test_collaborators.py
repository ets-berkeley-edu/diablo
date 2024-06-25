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
import copy
from datetime import timedelta

import pytest
from xena.models.recording_schedule import RecordingSchedule
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestCollaborators0:

    test_data = util.get_test_script_course('test_collaborators_0')
    section = util.get_test_section(test_data)
    meeting = section.meetings[0]
    meeting_room = copy.deepcopy(meeting.room)
    recording_schedule = RecordingSchedule(section, meeting)
    instructor = section.instructors[0]
    proxy = section.proxies[0]
    manual_collaborator = util.get_test_collaborator()

    def test_setup(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.section)
        util.reset_section_test_data(self.section)

        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()
        self.jobs_page.run_emails_job()
        util.reset_sent_email_test_data(self.section)

    def test_semester_start(self):
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()
        assert util.get_kaltura_id(self.recording_schedule)

    def test_kaltura_proxy_collaborator(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)
        self.kaltura_page.verify_collaborators(self.section, [self.proxy])

    def test_kaltura_proxy_collaborator_perms(self):
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy) == 'Co-Editor, Co-Publisher'

    def test_course_page_sis_data(self):
        self.jobs_page.load_page()
        self.jobs_page.log_out()
        self.login_page.dev_auth(self.instructor.uid)
        self.instructor_page.click_course_page_link(self.section)
        self.course_page.wait_for_instructors()
        assert self.course_page.visible_instructors() == [f'{self.instructor.first_name} {self.instructor.last_name}'.strip()]
        assert self.course_page.visible_proxies() == [f'{self.proxy.first_name} {self.proxy.last_name}'.strip()]

    def test_proxy_collaborator_by_default(self):
        assert self.course_page.visible_collaborator_uids() == [str(self.proxy.uid)]

    def test_add_collaborator(self):
        self.course_page.click_edit_collaborators()
        self.course_page.add_collaborator_by_uid(self.manual_collaborator)
        self.course_page.save_collaborator_edits()
        self.course_page.verify_collaborator_uids([self.proxy, self.manual_collaborator])

    def test_run_updates(self):
        self.course_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_new_collaborator(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)
        self.kaltura_page.verify_collaborators(self.section, [self.proxy, self.manual_collaborator])

    def test_kaltura_new_collaborator_perms(self):
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.manual_collaborator) == 'Co-Editor, Co-Publisher'

    def test_room_removed(self):
        util.change_course_room(self.section, self.meeting, new_room=None)

    def test_run_kaltura_job_room_removed(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_series_canceled_room_removed(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_title('Access Denied - UC Berkeley - Test')

    def test_room_restored(self):
        util.change_course_room(self.section, self.meeting, new_room=self.meeting_room)

    def test_run_kaltura_job_room_restored(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_collaborators_restored(self):
        util.get_kaltura_id(self.recording_schedule)
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_collaborators(self.section, [self.proxy, self.manual_collaborator])
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.manual_collaborator) == 'Co-Editor, Co-Publisher'


@pytest.mark.usefixtures('page_objects')
class TestCollaborators1:

    test_data = util.get_test_script_course('test_collaborators_1')
    section = util.get_test_section(test_data)
    meeting_0 = section.meetings[0]
    meeting_1 = section.meetings[1]

    meeting_0.meeting_schedule.end_date = (meeting_0.meeting_schedule.end_date - timedelta(days=15)).strftime('%Y-%m-%d')
    meeting_1.meeting_schedule.start_date = (meeting_0.meeting_schedule.end_date + timedelta(days=1)).strftime('%Y-%m-%d')

    recording_schedule_0 = RecordingSchedule(section, meeting_0)
    recording_schedule_1 = RecordingSchedule(section, meeting_1)
    instructor = section.instructors[0]
    proxy = section.proxies[0]
    manual_collaborator = util.get_test_collaborator()

    def test_setup(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.section)
        util.reset_section_test_data(self.section)
        util.delete_course_instructor_row(self.section, self.proxy)

        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()
        self.jobs_page.run_emails_job()
        util.reset_sent_email_test_data(self.section)

    def test_update_jobs(self):
        self.jobs_page.run_semester_start_job()
        assert util.get_kaltura_id(self.recording_schedule_0)
        assert util.get_kaltura_id(self.recording_schedule_1)

    def test_load_course_page(self):
        self.course_page.load_page(self.section)
        assert self.course_page.visible_instructors() == [f'{self.instructor.first_name} {self.instructor.last_name}'.strip()]
        assert self.course_page.visible_proxies() == []

    def test_add_collaborator(self):
        self.course_page.click_edit_collaborators()
        self.course_page.add_collaborator_by_uid(self.manual_collaborator)
        self.course_page.save_collaborator_edits()
        self.course_page.verify_collaborator_uids([self.manual_collaborator])

    def test_run_updates(self):
        self.course_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_new_collaborator_meeting_0(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_0.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section, [self.manual_collaborator])

    def test_kaltura_new_collaborator_meeting_1(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_1.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section, [self.manual_collaborator])

    def test_proxy_added(self):
        util.add_sis_sections_rows(self.section, instructors=[self.proxy])
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_new_proxy_meeting_0(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_0.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_0)
        self.kaltura_page.verify_collaborators(self.section, [self.manual_collaborator, self.proxy])

    def test_kaltura_new_proxy_meeting_1(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_1.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting_1)
        self.kaltura_page.verify_collaborators(self.section, [self.manual_collaborator, self.proxy])

    def test_course_page_new_proxy(self):
        self.course_page.load_page(self.section)
        self.course_page.wait_for_instructors()
        assert self.course_page.visible_instructors() == [f'{self.instructor.first_name} {self.instructor.last_name}'.strip()]
        assert self.course_page.visible_proxies() == [f'{self.proxy.first_name} {self.proxy.last_name}'.strip()]

    def test_new_collaborators(self):
        self.course_page.verify_collaborator_uids([self.proxy, self.manual_collaborator])

    def test_remove_collaborator(self):
        self.course_page.click_edit_collaborators()
        self.course_page.click_remove_collaborator(self.manual_collaborator)
        self.course_page.save_collaborator_edits()

    def test_run_updates_remove_collaborator(self):
        self.jobs_page.load_page()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_collaborator_removed_meeting_0(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_0.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_collaborators(self.section, [self.proxy])
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy) == 'Co-Editor, Co-Publisher'

    def test_kaltura_collaborator_removed_meeting_1(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule_1.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_collaborators(self.section, [self.proxy])
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy) == 'Co-Editor, Co-Publisher'


@pytest.mark.usefixtures('page_objects')
class TestCollaborators2:

    test_data = util.get_test_script_course('test_collaborators_2')
    section = util.get_test_section(test_data)
    meeting = section.meetings[0]
    recording_schedule = RecordingSchedule(section, meeting)
    instructor = section.instructors[0]
    proxy_0 = section.proxies[0]
    proxy_1 = section.proxies[1]

    def test_setup(self):
        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(self.section)
        util.reset_section_test_data(self.section)

        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()
        self.jobs_page.run_emails_job()
        util.reset_sent_email_test_data(self.section)

    def test_run_updates(self):
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()
        util.get_kaltura_id(self.recording_schedule)

    def test_kaltura_proxy_collaborator(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)
        self.kaltura_page.verify_collaborators(self.section, self.section.proxies)

    def test_kaltura_proxy_collaborator_perms(self):
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy_0) == 'Co-Editor, Co-Publisher'
        assert self.kaltura_page.collaborator_perm(self.proxy_1) == 'Co-Editor, Co-Publisher'

    def test_course_page_sis_data(self):
        self.jobs_page.load_page()
        self.jobs_page.log_out()
        self.login_page.dev_auth(self.instructor.uid)
        self.instructor_page.click_course_page_link(self.section)
        self.course_page.wait_for_instructors()
        assert self.course_page.visible_instructors() == [f'{self.instructor.first_name} {self.instructor.last_name}'.strip()]
        assert self.course_page.visible_proxies() == [f'{p.first_name} {p.last_name}'.strip() for p in self.section.proxies]

    def test_proxy_collaborators_by_default(self):
        self.course_page.verify_collaborator_uids(self.section.proxies)

    def test_remove_proxy(self):
        self.course_page.click_edit_collaborators()
        self.course_page.click_remove_collaborator(self.proxy_0)
        self.course_page.save_collaborator_edits()

    def test_run_updates_proxy_collaborator_removed(self):
        self.course_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_proxy_collaborator_removed(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)
        self.kaltura_page.verify_collaborators(self.section, [self.proxy_1])

    def test_remove_other_proxy(self):
        util.delete_course_instructor_row(self.section, self.proxy_1)

    def test_run_updates_no_proxies(self):
        self.jobs_page.load_page()
        self.jobs_page.run_schedule_updates_job()
        self.jobs_page.run_kaltura_job()

    def test_kaltura_no_proxy_collaborators(self):
        self.kaltura_page.load_event_edit_page(self.recording_schedule.series_id)
        self.kaltura_page.wait_for_delete_button()
        self.kaltura_page.verify_title_and_desc(self.section, self.meeting)
        self.kaltura_page.verify_collaborators(self.section, [])

    def test_kaltura_no_proxy_collaborator_perms(self):
        assert self.kaltura_page.collaborator_perm(self.instructor) == 'Co-Editor, Co-Publisher'
