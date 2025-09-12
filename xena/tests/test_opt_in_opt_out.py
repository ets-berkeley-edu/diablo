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

from datetime import timedelta

import pytest

from xena.models.email_template_type import EmailTemplateType
from xena.models.recording_schedule import RecordingSchedule
from xena.test_utils import util

sections = util.get_test_opt_out_sections()

# Section with single instructor and single meeting
section_0 = sections[0]
instructor_0 = section_0.instructors[0]
recording_schedule_0 = RecordingSchedule(section_0, section_0.meetings[0])

# Co-taught section with two meetings
section_1 = sections[1]
instructor_1_0, instructor_1_1 = section_1.instructors[0], section_1.instructors[1]
meeting_1_0, meeting_1_1 = section_1.meetings[0], section_1.meetings[1]
meeting_1_0_sched, meeting_1_1_sched = meeting_1_0.meeting_schedule, meeting_1_1.meeting_schedule
meeting_1_0_sched.end_date = meeting_1_0_sched.end_date - timedelta(days=8)
meeting_1_1_sched.start_date = meeting_1_0_sched.end_date + timedelta(days=1)
recording_schedule_1_0 = RecordingSchedule(section_1, meeting_1_0)
recording_schedule_1_1 = RecordingSchedule(section_1, meeting_1_1)

# Extra instructor
instructor_1_2 = util.get_test_instructors(1, uids_to_exclude=[instructor_1_0.uid, instructor_1_1.uid])

@pytest.mark.usefixtures('page_objects')
class TestOptIn0:
    """
    SCENARIO.

    - Instructor opts out by default, accepts reminder emails
    - Instructor receives new-course-eligible email and later an opted-out reminder
    - Instructor opts in, recordings are scheduled, and instructor later receives scheduled reminder
    - Instructor is removed in SIS, recordings are unscheduled
    - Admin manually schedules the instructor-less course
    - Admin manually un-schedules the instructor-less course
    """

    def test_set_up(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.disable_all_jobs()
        self.jobs_page.run_emails_job()
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_0)

        self.kaltura_page.log_in_via_calnet(self.calnet_page)
        self.kaltura_page.reset_test_data(section_0)

        util.reset_section_test_data(section_0)
        util.reset_user_preferences(instructor_0)

    def test_initial_job_runs(self):
        self.ouija_page.load_page()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_instructor_new_course_eligible_email(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_0) == 1

    def test_remind_opt_outs_job(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_instructor_remind_opt_outs_email(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                         instructor=instructor_0) == 1

    def test_instructor_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_0)
        # TODO verifies default settings, opts in

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0)

    def test_remind_scheduled_job(self):
        self.jobs_page.run_remind_scheduled_job_sequence()

    def test_instructor_remind_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_SCHEDULED, section=None,
                                         instructor=instructor_0) == 1

    def test_instructor_removed(self):
        util.change_course_instructor(section_0, old_instructor=instructor_0, new_instructor=None)
        section_0.instructors = []

    def test_unschedule_recordings(self):
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_unscheduled(self):
        assert not util.get_kaltura_id(recording_schedule_0)

    # TODO - admin manually reschedules the instructor-less course
    # TODO - additional job runs do not unschedule the course automatically
    # TODO - admin manually un-schedules the instructor-less course


@pytest.mark.usefixtures('page_objects')
class TestOptIn1:
    """
    SCENARIO.

     - Instructor opts out by default, does not want reminder emails
     - Instructor receives new-course-eligible email but does not receive opted-out reminder
     - Instructor opts in, recordings are scheduled, and instructor later receives scheduled reminder
     - Instructor opts out, recordings are unscheduled, and instructor receives course-opted-out email
     - Instructor later receives opted-out reminder
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_0)
        self.kaltura_page.reset_test_data(section_0)
        util.reset_section_test_data(section_0, delete_opt_ins=True)
        util.reset_user_preferences(instructor_0)

    def test_instructor_rejects_reminders(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(instructor_0)
        # TODO - check "no more email" box

    def test_instructor_new_course_eligible_email(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None, instructor=instructor_0) == 1

    def test_instructor_no_opt_out_reminder_email(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None, instructor=instructor_0) == 0

    def test_instructor_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_0)
        # TODO - opts in
        # TODO - verify no-email checkbox vanishes

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0)

    def test_remind_scheduled_job(self):
        self.jobs_page.run_remind_scheduled_job_sequence()

    def test_instructor_remind_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_SCHEDULED, section=None,
                                         instructor=instructor_0) == 1

    def test_instructor_opts_back_out(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_0)
        # TODO - opt out again, don't recheck no-emails box

    def test_unschedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_unscheduled(self):
        assert not util.get_kaltura_id(recording_schedule_0)

    def test_instructor_opted_out_email(self):
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_0,
                                         instructor=instructor_0) == 1

    def test_send_opted_out_reminders(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                         instructor=instructor_0) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptIn2:
    """
    SCENARIO.

    - Instructor opts in by default
    - Instructor receives new-course-eligible email, recordings are automatically scheduled
    - Instructor later receives scheduled reminder
    - Instructor opts out, recordings are unscheduled, and instructor receives opted-out email
    - Instructor later receives opted-out reminder
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_0)
        self.kaltura_page.reset_test_data(section_0)
        util.reset_section_test_data(section_0, delete_opt_ins=True)
        util.reset_user_preferences(instructor_0)

    def test_opt_in_all(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(instructor_0)
        # TODO - opt in all

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0)

    def test_instructor_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_0,
                                         instructor=instructor_0) == 1

    def test_instructor_opts_out(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_0)
        # TODO - opt out course

    def test_unschedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_unscheduled(self):
        assert not util.get_kaltura_id(recording_schedule_0)

    def test_instructor_opted_out_email(self):
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_0,
                                         instructor=instructor_0) == 1

    def test_remind_opt_outs(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_instructor_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                         instructor=instructor_0) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptIn3:
    """
    SCENARIO.

    - A section has no instructor, and recordings are not scheduled
    - An instructor who has opted in for all terms is added to the section
    - Recordings are scheduled, and the instructor receives a new-course-scheduled email
    - An instructor who opts out by default is added to the section
    - Recordings are unscheduled, and the instructors both receive an opted-out confirmation and partially approved reminder
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_0)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_1, delete_opt_ins=True)
        util.reset_user_preferences(instructor_1_0)
        util.reset_user_preferences(instructor_1_1)
        util.change_course_instructor(section_1, old_instructor=None, new_instructor=None)

    def test_instructor_opt_in_all(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt in for all

    def test_add_instructor(self):
        util.change_course_instructor(section_1, old_instructor=None, new_instructor=instructor_1_0)
        section_1.instructors = [instructor_1_0]

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_0) == 1
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_add_another_instructor(self):
        util.add_sis_sections_rows(section_1, [instructor_1_1])

    def test_unschedule_recordings(self):
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_unscheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1_0)
        assert not util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_0_course_unscheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_1,
                                         instructor=instructor_1_0) == 1
        # A second new-course-eligible email is not sent to Inst 1
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_course_unscheduled_emails(self):
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_1,
                                         instructor=instructor_1_1) == 1
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_1) == 1

    def test_remind_opt_outs(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_instructor_0_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                         instructor=instructor_1_0) == 0

    def test_instructor_1_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                         instructor=instructor_1_1) == 1

    def test_remind_partially_approved(self):
        self.jobs_page.run_remind_partially_approved_job_sequence()

    def test_instructor_0_partially_approved_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_0,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_partially_approved_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_0,
                                         instructor=instructor_1_1) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptIn4:
    """
    SCENARIO.

    - A section has two primary instructors, both opted out by default but accepting reminder emails
    - Both receive new-course-eligible email and later opted-out reminder
    - Instructor 1 opts in, and later both receive partially-approved reminder
    - Instructor 2 opts in, recordings are scheduled, and both receive new-course-scheduled confirmation
    - Both receive scheduled reminder
    - Instructor 2 is removed. Recordings remain scheduled, and there is no email.
    - Instructor 3 is added, who is opted out by default.
    - Recordings are unscheduled, and opted-out confirmation is sent to both.
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_1)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_1)
        util.reset_user_preferences(instructor_1_0)
        util.reset_user_preferences(instructor_1_1)

    def test_run_schedule_update(self):
        self.ouija_page.load_page()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_instructor_0_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_1) == 1

    def test_instructor_0_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt in

    def test_run_remind_partially_approved_job(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_remind_partially_approved_job_sequence()

    def test_instructor_0_partially_approved_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_partially_approved_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_1,
                                         instructor=instructor_1_1) == 1

    def test_instructor_1_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_1)
        # TODO - opt in

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_0_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_1) == 1

    def test_run_remind_scheduled_job(self):
        self.jobs_page.run_remind_scheduled_job_sequence()

    def test_instructor_0_scheduled_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_SCHEDULED, section=None,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_scheduled_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_SCHEDULED, section=None,
                                         instructor=instructor_1_1) == 1

    def test_instructor_1_removed(self):
        util.change_course_instructor(section_1, old_instructor=instructor_1_1, new_instructor=None)

    def test_run_schedule_update_job(self):
        self.jobs_page.run_schedule_update_job_sequence()

    def test_instructor_1_removal_email(self):
        assert util.get_sent_email_count(EmailTemplateType.INSTRUCTORS_REMOVED, section=section_1,
                                         instructor=instructor_1_1) == 1

    def test_recordings_still_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_2_added(self):
        util.add_sis_sections_rows(section_1, instructor_1_2)

    def test_unschedule_recordings(self):
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_unscheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1_0)
        assert not util.get_kaltura_id(recording_schedule_1_0)

    def test_instructor_0_opt_out_email(self):
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_2_opt_out_email(self):
        assert util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_1,
                                         instructor=instructor_1_2) == 1

    def test_instructor_2_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_2) == 1


@pytest.mark.usefixtures('page_objects')
class TestOptIn5:
    """
    SCENARIO.

    - A section has a primary instructor and ICNT, both opted out by default and only the former accepting reminder emails
    - Both receive new-course-eligible email and later just one receives an opted-out reminder
    - Instructor 1 opts in and later receives a partially-approved reminder. Instructor 2 receives nothing.
    - Instructor 1 opts out and later receives an opted-out reminder. Instructor 2 receives nothing.
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_1)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_1)
        util.reset_user_preferences(instructor_1_0)
        util.reset_user_preferences(instructor_1_1)
        util.set_instructor_role(section_1, instructor_1_1, 'ICNT')

    def test_decline_reminder_emails(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - no reminders

    def test_run_schedule_updates(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_not_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1_0)
        assert not util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_0_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_1) == 1

    def test_run_opt_out_reminders(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_instructor_0_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_no_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=section_1,
                                         instructor=instructor_1_1) == 0

    def test_instructor_0_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt in

    def test_run_settings_update(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_still_not_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1_0)
        assert not util.get_kaltura_id(recording_schedule_1_1)

    def test_run_partially_approved_reminders(self):
        self.jobs_page.run_remind_partially_approved_job_sequence()

    def test_instructor_0_partial_approval_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_no_partial_approval_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_1,
                                         instructor=instructor_1_1) == 0

    def test_instructor_0_opts_out(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt out

    def test_run_settings_update_again(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_instructor_0_no_opt_out_email(self):
        assert not util.get_sent_email_count(EmailTemplateType.OPTED_OUT, section=section_1,
                                             instructor=instructor_1_0) == 0

    def test_run_opted_out_reminders_again(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_instructor_0_opt_out_reminder_again(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=section_1,
                                         instructor=instructor_1_0) == 2

    def test_instructor_1_still_no_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=section_1,
                                         instructor=instructor_1_1) == 0


@pytest.mark.usefixtures('page_objects')
class TestOptIn6:
    """
    SCENARIO.

    - A course has two primary instructors, one opt-in by default, the other opt-out by default and not accepting reminders
    - Both receive new-course-eligible email and later just one receives a partially-approved reminder
    - Instructor 2 opts in, and recordings are scheduled.
    - Both receive new-course-scheduled confirmation.
    - Instructor 1 switches to opt-out by default, and recordings remain scheduled.
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_1)
        self.kaltura_page.reset_test_data(section_1)
        util.reset_section_test_data(section_1)
        util.reset_user_preferences(instructor_1_0)
        util.reset_user_preferences(instructor_1_1)

    def test_instructor_0_opt_in_for_all(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt in for all

    def test_instructor_1_decline_reminder_emails(self):
        self.courses_page.log_out()
        self.login_page.dev_auth(instructor_1_1)
        # TODO - no reminders

    def test_run_schedule_updates(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_recordings_not_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1_0)
        assert not util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_0_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_1) == 1

    def test_run_opt_out_reminder(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_no_opt_out_reminders(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=section_1,
                                         instructor=instructor_1_0) == 0
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=section_1,
                                         instructor=instructor_1_1) == 0

    def test_run_partially_approved_reminder(self):
        self.jobs_page.run_remind_partially_approved_job_sequence()

    def test_instructor_0_partial_approval_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_partial_approval_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=section_1,
                                         instructor=instructor_1_1) == 0

    def test_instructor_1_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_1)
        # TODO opt in
        # TODO verify no-reminders option vanishes

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_0_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_1) == 1

    def test_run_remind_scheduled(self):
        self.jobs_page.run_remind_scheduled_job_sequence()

    def test_instructor_0_reminder_email(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_SCHEDULED, section=None,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_reminder_email(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_SCHEDULED, section=None,
                                         instructor=instructor_1_1) == 1

    def test_instructor_0_removes_opt_in_all(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO remove opt-in-all

    def test_run_settings_update(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_still_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)


@pytest.mark.usefixtures('page_objects')
class TestOptIn7:
    """
    SCENARIO.

    - A course has a primary instructor and a proxy
    - The instructor is opt-out by default and accepts reminders; the proxy is opt-in by default
    - Only the instructor receives a new-course-eligible email and later an opted-out reminder but no partial approval reminder
    - The instructor opts in, recordings are scheduled, and only the instructor receives the new course scheduled confirmation
    """

    def test_set_up(self):
        util.reset_sent_email_test_data(section_1)
        util.reset_sent_email_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        self.kaltura_page.reset_test_data(section_0)
        util.reset_section_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.change_course_instructor(section_0, old_instructor=None, new_instructor=instructor_1_1)
        util.set_instructor_role(section_1, instructor_1_1, 'APRX')

        util.reset_sent_email_test_data(section=None, instructor=instructor_1_0)
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_1)
        util.reset_user_preferences(instructor_1_0)
        util.reset_user_preferences(instructor_1_1)

    def test_instructor_1_opts_in_for_all(self):
        self.ouija_page.load_page()
        self.ouija_page.log_out()
        self.login_page.dev_auth(instructor_1_1)
        # TODO - opt in for all

    def test_run_schedule_update(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_section_0_not_scheduled(self):
        assert not util.get_kaltura_id(recording_schedule_1_0)
        assert not util.get_kaltura_id(recording_schedule_1_1)

    def test_section_1_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_0)

    def test_instructor_0_new_course_eligible(self):
        assert util.get_sent_email_count(EmailTemplateType.NEW_CLASS_ELIGIBLE, section=None,
                                         instructor=instructor_1_0) == 1

    def test_run_opt_out_reminder(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_instructor_0_opt_out_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                         instructor=instructor_1_0) == 1

    def test_run_partial_approval_reminder(self):
        self.jobs_page.run_remind_partially_approved_job_sequence()

    def test_instructor_0_no_partial_approval_reminder(self):
        assert util.get_sent_email_count(EmailTemplateType.REMIND_PARTIALLY_APPROVED, section=None,
                                         instructor=instructor_1_0)

    def test_instructor_0_opts_in(self):
        self.jobs_page.log_out()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt in

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_settings_update_job_sequence()

    def test_recordings_scheduled(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)

    def test_instructor_0_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_0) == 1

    def test_instructor_1_no_course_scheduled_email(self):
        assert util.get_sent_email_count(EmailTemplateType.CLASS_SCHEDULED, section=section_1,
                                         instructor=instructor_1_1) == 0


@pytest.mark.usefixtures('page_objects')
class TestOptIn8:
    """
    SCENARIO.

    - An instructor is teaching two courses and opts out by default but accepts reminder emails.
    - The instructor opts in for one course but not the other.
    - The instructor receives no opted-out reminder
    """

    def test_setup(self):
        util.reset_sent_email_test_data(section_1)
        util.reset_sent_email_test_data(section_0)
        self.kaltura_page.reset_test_data(section_1)
        self.kaltura_page.reset_test_data(section_0)
        util.reset_section_test_data(section_1)
        util.reset_section_test_data(section_0)
        util.delete_sis_sections_rows(section_1)
        util.delete_sis_sections_rows(section_0)
        util.add_sis_sections_rows(section_1, [instructor_1_0])
        util.add_sis_sections_rows(section_0, [instructor_1_0])
        util.reset_sent_email_test_data(section=None, instructor=instructor_1_0)
        util.reset_user_preferences(instructor_1_0)

    def test_opt_in_for_one(self):
        self.ouija_page.load_page()
        self.login_page.dev_auth(instructor_1_0)
        # TODO - opt in one course only

    def test_schedule_recordings(self):
        self.courses_page.log_out()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    def test_one_course_scheduled_only(self):
        assert util.get_kaltura_id(recording_schedule_1_0)
        assert util.get_kaltura_id(recording_schedule_1_1)
        assert not util.get_kaltura_id(recording_schedule_0)

    def test_run_opt_out_reminders(self):
        self.jobs_page.run_remind_opt_outs_job_sequence()

    def test_no_opted_out_reminder(self):
        assert not util.get_sent_email_count(EmailTemplateType.REMIND_OPTED_OUT, section=None,
                                             instructor=instructor_1_0)
