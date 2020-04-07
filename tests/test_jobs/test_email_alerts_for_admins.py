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
from diablo.jobs.admin_emails_job import AdminEmailsJob
from diablo.models.approval import Approval
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from flask import current_app as app


class TestEmailAlertsForAdmins:

    def test_alert_admin_of_room_change(self):
        """Emails admin when a scheduled course gets a room change."""
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 26094

        the_old_room = 'Wheeler 150'

        scheduled_in_room = Room.find_room(the_old_room)
        approval = Approval.create(
            approved_by_uid='6789',
            term_id=term_id,
            section_id=section_id,
            approver_type_='instructor',
            publish_type_='kaltura_media_gallery',
            recording_type_='presenter_audio',
            room_id=scheduled_in_room.id,
        )
        scheduled = Scheduled.create(
            term_id=term_id,
            section_id=section_id,
            room_id=scheduled_in_room.id,
        )
        email_count = _get_email_count()
        AdminEmailsJob(app.app_context).run()
        assert _get_email_count() == email_count + 1

        # Clean up
        Approval.delete(approval)
        Scheduled.delete(scheduled)

    def test_alert_admin_of_instructor_change(self):
        """Emails admin when a scheduled course gets a new instructor."""
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 22287
        room_id = Room.find_room('Barker 101').id

        approval = Approval.create(
            approved_by_uid='98765',
            term_id=term_id,
            section_id=section_id,
            approver_type_='instructor',
            publish_type_='canvas',
            recording_type_='presenter_audio',
            room_id=room_id,
        )
        scheduled = Scheduled.create(
            term_id=term_id,
            section_id=section_id,
            room_id=room_id,
        )
        email_count = _get_email_count()
        AdminEmailsJob(app.app_context).run()
        assert _get_email_count() == email_count + 1

        # Clean up
        Approval.delete(approval)
        Scheduled.delete(scheduled)


def _get_email_count():
    admin_uid = app.config['EMAIL_DIABLO_ADMIN_UID']
    return len(SentEmail.get_emails_sent_to(uid=admin_uid))
