"""
Copyright ©2020. The Regents of the University of California (Regents). All Rights Reserved.

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
import random

from diablo import std_commit
from diablo.jobs.admin_emails_job import AdminEmailsJob
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.doomed_to_failure import DoomedToFailure
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date, is_schedule_obsolete
from diablo.models.approval import Approval
from diablo.models.job import Job
from diablo.models.queued_email import QueuedEmail
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
import pytest
from tests.test_api.api_test_utils import get_eligible_meeting, get_instructor_uids, mock_scheduled
from tests.util import override_config, simply_yield, test_approvals_workflow


@pytest.fixture()
def enable_admin_emails():
    all_jobs = Job.get_all(include_disabled=True)
    admin_emails_job = next((j for j in all_jobs if j.key == AdminEmailsJob.key()))
    Job.update_disabled(job_id=admin_emails_job.id, disable=False)
    std_commit(allow_test_environment=True)


class TestEmailAlertsForAdmins:

    def test_admin_alert_date_change(self, db_session, enable_admin_emails):
        admin_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50004
        meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    def _run_jobs():
                        AdminEmailsJob(simply_yield).run()
                        QueuedEmailsJob(simply_yield).run()

                    def _schedule():
                        mock_scheduled(
                            meeting=meeting,
                            override_end_time='16:59',
                            override_start_time='08:00',
                            section_id=section_id,
                            term_id=term_id,
                        )
                        course = SisSection.get_course(section_id=section_id, term_id=term_id)
                        assert is_schedule_obsolete(meeting=meeting, scheduled=course['scheduled'])

                    def _assert_alert_count(count):
                        emails_sent = SentEmail.get_emails_sent_to(uid=admin_uid)
                        assert len(emails_sent) == count
                        assert emails_sent[0].section_id == section_id
                        assert emails_sent[0].template_type == 'admin_alert_date_change'

                    # First time scheduled.
                    _schedule()
                    _run_jobs()
                    _assert_alert_count(1)
                    # Unschedule and schedule a second time.
                    Scheduled.delete(section_id=section_id, term_id=term_id)
                    _schedule()
                    _run_jobs()
                    # Another alert is emailed to admin because it is a new schedule.
                    _assert_alert_count(2)
                    # Run jobs again and expect no alerts.
                    _run_jobs()
                    _assert_alert_count(2)

    def test_alert_admin_of_room_change(self, db_session, enable_admin_emails):
        """Emails admin when a scheduled course gets a room change."""
        with test_approvals_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            section_id = 50004
            approved_by_uid = '10004'
            the_old_room = 'Wheeler 150'
            scheduled_in_room = Room.find_room(the_old_room)
            approval = Approval.create(
                approved_by_uid=approved_by_uid,
                approver_type_='instructor',
                publish_type_='kaltura_media_gallery',
                recording_type_='presenter_audio',
                room_id=scheduled_in_room.id,
                section_id=section_id,
                term_id=term_id,
            )
            meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
            Scheduled.create(
                instructor_uids=get_instructor_uids(term_id=term_id, section_id=section_id),
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                meeting_start_time=meeting['startTime'],
                publish_type_=approval.publish_type,
                recording_type_=approval.recording_type,
                room_id=scheduled_in_room.id,
                section_id=section_id,
                term_id=term_id,
            )

            admin_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
            # Message queued, then sent.
            AdminEmailsJob(simply_yield).run()
            QueuedEmailsJob(simply_yield).run()
            emails_sent = SentEmail.get_emails_sent_to(uid=admin_uid)
            assert len(emails_sent) == 1
            assert emails_sent[0].section_id == section_id
            assert emails_sent[0].template_type == 'admin_alert_room_change'

    def test_alert_admin_of_instructor_change(self, enable_admin_emails):
        """Emails admin when a scheduled course gets a new instructor."""
        with test_approvals_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            section_id = 50005
            room_id = Room.find_room('Barker 101').id
            # The course has two instructors.
            instructor_1_uid, instructor_2_uid = get_instructor_uids(section_id=section_id, term_id=term_id)
            approval = Approval.create(
                approved_by_uid=instructor_1_uid,
                approver_type_='instructor',
                publish_type_='kaltura_my_media',
                recording_type_='presenter_audio',
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )
            # Uh oh! Only one of them has been scheduled.
            meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
            Scheduled.create(
                instructor_uids=[instructor_1_uid],
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                meeting_start_time=meeting['startTime'],
                publish_type_=approval.publish_type,
                recording_type_=approval.recording_type,
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )
            admin_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
            email_count = _get_email_count(admin_uid)
            # Message queued but not sent.
            AdminEmailsJob(simply_yield).run()
            assert _get_email_count(admin_uid) == email_count
            queued_messages = QueuedEmail.query.filter_by(template_type='admin_alert_instructor_change').all()
            assert len(queued_messages) == 1
            for snippet in ['LAW 23', 'Old instructor(s) Regan MacNeil', 'New instructor(s) Regan MacNeil, Burke Dennings']:
                assert snippet in queued_messages[0].message
            # Message sent.
            QueuedEmailsJob(simply_yield).run()
            assert _get_email_count(admin_uid) == email_count + 1

    def test_admin_alert_multiple_meeting_patterns(self, enable_admin_emails):
        """Emails admin if course is scheduled with weird start/end dates."""
        with test_approvals_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            section_id = 50014
            room_id = Room.find_room('Barker 101').id
            # The course has two instructors.
            instructor_uid = get_instructor_uids(section_id=section_id, term_id=term_id)[0]
            approval = Approval.create(
                approved_by_uid=instructor_uid,
                approver_type_='instructor',
                publish_type_='kaltura_my_media',
                recording_type_='presenter_audio',
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )
            # Uh oh! Only one of them has been scheduled.
            meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
            Scheduled.create(
                instructor_uids=[instructor_uid],
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                meeting_start_time=meeting['startTime'],
                publish_type_=approval.publish_type,
                recording_type_=approval.recording_type,
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )
            courses = SisSection.get_courses_scheduled_nonstandard_dates(term_id=term_id)
            course = next((c for c in courses if c['sectionId'] == section_id), None)
            assert course

            # Message queued but not sent.
            admin_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
            AdminEmailsJob(simply_yield).run()
            queued_messages = QueuedEmail.query.filter_by(section_id=section_id).all()
            assert len(queued_messages) == 1
            for queued_message in queued_messages:
                assert '2020-08-26 to 2020-10-02' in queued_message.message

            # Message sent.
            QueuedEmailsJob(simply_yield).run()
            emails_sent = SentEmail.get_emails_sent_to(uid=admin_uid)
            assert len(emails_sent) == 1
            assert emails_sent[0].template_type == 'admin_alert_multiple_meeting_patterns'
            assert emails_sent[0].section_id == section_id

    def test_alert_on_job_failure(self):
        admin_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
        email_count = _get_email_count(admin_uid)
        # No alert on happy job.
        CanvasJob(simply_yield).run()
        assert _get_email_count(admin_uid) == email_count
        # Alert on sad job.
        all_jobs = Job.get_all(include_disabled=True)
        doomed_job = next((j for j in all_jobs if j.key == DoomedToFailure.key()))

        # Make sure job is enabled
        Job.update_disabled(job_id=doomed_job.id, disable=False)
        std_commit(allow_test_environment=True)
        DoomedToFailure(simply_yield).run()
        # Failure alerts do not go through the queue.
        assert _get_email_count(admin_uid) == email_count + 1


def _get_email_count(uid):
    return len(SentEmail.get_emails_sent_to(uid=uid))
