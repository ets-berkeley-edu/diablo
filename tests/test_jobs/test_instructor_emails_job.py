"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.jobs.instructor_emails_job import InstructorEmailsJob
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.test_api.api_test_utils import mock_scheduled
from tests.util import enabled_job, simply_yield, test_approvals_workflow


class TestInstructorEmailsJob:

    def test_room_change_no_longer_eligible(self, db_session):
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50004

        def _schedule(room_id):
            mock_scheduled(
                override_room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )

        def _assert_alert_count(template_type, count):
            emails_sent = SentEmail.get_emails_of_type(
                section_ids=[section_id],
                template_type=template_type,
                term_id=term_id,
            )
            assert len(emails_sent) == count

        with enabled_job(job_key=InstructorEmailsJob.key()):
            with test_approvals_workflow(app):
                course = SisSection.get_course(section_id=section_id, term_id=term_id)
                eligible_meetings = course.get('meetings', {}).get('eligible', [])
                assert eligible_meetings
                room_id = eligible_meetings[0]['room']['id']

                # Schedule
                _schedule(room_id)
                InstructorEmailsJob(simply_yield).run()
                QueuedEmailsJob(simply_yield).run()
                _assert_alert_count('room_change_no_longer_eligible', 0)

                # Unschedule.
                Scheduled.delete(section_id=section_id, term_id=term_id)
                # Schedule to an eligible room.
                _schedule(Room.find_room('Barker 101').id)
                InstructorEmailsJob(simply_yield).run()
                QueuedEmailsJob(simply_yield).run()
                # Expect no email.
                _assert_alert_count('room_change_no_longer_eligible', 0)

                # Unschedule.
                Scheduled.delete(section_id=section_id, term_id=term_id)
                # Schedule to an ineligible room.
                _schedule(Room.find_room('Wheeler 150').id)
                InstructorEmailsJob(simply_yield).run()
                QueuedEmailsJob(simply_yield).run()
                # Expect email.
                _assert_alert_count('room_change_no_longer_eligible', 1)


def _get_email_count(uid):
    return len(SentEmail.get_emails_sent_to(uid=uid))
