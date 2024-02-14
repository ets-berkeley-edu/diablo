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
import random

from diablo import std_commit
from diablo.jobs.remind_invitees_job import RemindInviteesJob
from diablo.jobs.tasks.invitation_emails_task import InvitationEmailsTask
from diablo.jobs.tasks.queued_emails_task import QueuedEmailsTask
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from diablo.lib.util import utc_now
from diablo.models.approval import Approval
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from tests.test_api.api_test_utils import get_eligible_meeting, get_instructor_uids
from tests.util import simply_yield, test_approvals_workflow


class TestInvitationEmailsTask:

    def test_remind_invitee(self, app):
        """Send reminder to instructors who have not RSVPed to original invitation."""
        _assert_reminder_to_invitees(app=app, schedule_recordings_before_assert=False)

    def test_no_reminder_invitee_when_scheduled(self, app):
        """Send reminder to instructors who have not RSVPed to original invitation."""
        _assert_reminder_to_invitees(app=app, schedule_recordings_before_assert=True)

    def test_no_reminder_before_invites_sent(self, app):
        """Send reminder to instructors who have not RSVPed to original invitation."""
        with test_approvals_workflow(app):
            timestamp = utc_now()
            # Send reminders. Expect only one sent for target section.
            RemindInviteesJob(simply_yield).run()
            QueuedEmailsTask().run()
            assert not _get_emails_sent_since(
                template_type='remind_invitees',
                term_id=app.config['CURRENT_TERM_ID'],
                timestamp=timestamp,
            )


def _assert_reminder_to_invitees(app, schedule_recordings_before_assert):
    with test_approvals_workflow(app):
        timestamp = utc_now()
        # Send invitations
        InvitationEmailsTask().run()
        QueuedEmailsTask().run()
        # Target a specific section_id.
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50000
        section = SisSection.get_course(section_id=section_id, term_id=term_id)
        invitations = _get_emails_sent_since(
            template_type='invitation',
            term_id=term_id,
            timestamp=timestamp,
        )
        # Isolate specific invitations.
        invitations_of_specific_section = list(filter(lambda e: e.section_id == section_id, invitations))
        # Expect the course to have two instructors.
        recipient_uids = [i.recipient_uid for i in invitations_of_specific_section]
        assert len(recipient_uids) == 2
        uid_1 = recipient_uids[0]
        uid_2 = recipient_uids[1]
        # One instructor approves
        room_id = section['meetings']['eligible'][0]['room']['id']
        Approval.create(
            approved_by_uid=uid_1,
            approver_type_='instructor',
            course_display_name='Foo',
            publish_type_='kaltura_my_media',
            recording_type_='presentation_audio',
            room_id=room_id,
            section_id=section_id,
            term_id=term_id,
        )
        std_commit(allow_test_environment=True)
        if schedule_recordings_before_assert:
            _schedule_recordings(room_id, section_id, term_id)
        # Send reminders. Expect only one sent for target section.
        RemindInviteesJob(simply_yield).run()
        QueuedEmailsTask().run()
        reminders = _get_emails_sent_since(
            template_type='remind_invitees',
            term_id=term_id,
            timestamp=timestamp,
        )
        reminders_of_specific_section = list(filter(lambda e: e.section_id == section_id, reminders))
        if schedule_recordings_before_assert:
            assert len(reminders_of_specific_section) == 0
        else:
            assert len(reminders_of_specific_section) == 1
            assert reminders_of_specific_section[0].recipient_uid == uid_2


def _get_emails_sent_since(template_type, term_id, timestamp):
    return SentEmail.query \
        .filter_by(template_type=template_type, term_id=term_id) \
        .filter(SentEmail.sent_at >= timestamp) \
        .order_by(SentEmail.sent_at).all()


def _schedule_recordings(room_id, section_id, term_id):
    meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
    Scheduled.create(
        course_display_name=f'term_id:{term_id} section_id:{section_id}',
        instructor_uids=get_instructor_uids(term_id=term_id, section_id=section_id),
        kaltura_schedule_id=random.randint(1, 10),
        meeting_days=meeting['days'],
        meeting_end_date=get_recording_end_date(meeting),
        meeting_end_time=meeting['endTime'],
        meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
        meeting_start_time=meeting['startTime'],
        publish_type_='kaltura_media_gallery',
        recording_type_='presenter_audio',
        room_id=room_id,
        section_id=section_id,
        term_id=term_id,
    )
