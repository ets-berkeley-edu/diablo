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
from diablo import db
from diablo.jobs.instructor_emails_job import InstructorEmailsJob
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy import text
from tests.test_api.api_test_utils import mock_scheduled
from tests.util import enabled_job, simply_yield, test_approvals_workflow


class TestInstructorEmailsJob:

    def test_room_change_no_longer_eligible(self, db_session):
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50004

        def _assert_email_count(template_type, expected_count):
            emails_sent = SentEmail.get_emails_of_type(
                section_ids=[section_id],
                template_type=template_type,
                term_id=term_id,
            )
            assert len(emails_sent) == expected_count

        def _move_course(meeting_location):
            db.session.execute(
                text('UPDATE sis_sections SET meeting_location = :meeting_location WHERE term_id = :term_id AND section_id = :section_id'),
                {
                    'meeting_location': meeting_location,
                    'section_id': section_id,
                    'term_id': term_id,
                },
            )

        def _run_instructor_emails_job():
            InstructorEmailsJob(simply_yield).run()
            QueuedEmailsJob(simply_yield).run()

        def _schedule(room_id):
            mock_scheduled(
                override_room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )

        with enabled_job(job_key=InstructorEmailsJob.key()):
            with test_approvals_workflow(app):
                course = SisSection.get_course(section_id=section_id, term_id=term_id)
                eligible_meetings = course.get('meetings', {}).get('eligible', [])
                assert len(eligible_meetings) == 1
                original_room = eligible_meetings[0]['room']
                assert original_room['location'] == 'Li Ka Shing 145'

                # Schedule
                _schedule(original_room['id'])
                _run_instructor_emails_job()
                _assert_email_count('room_change_no_longer_eligible', 0)

                # Move course to some other eligible room.
                _move_course('Barker 101')
                _run_instructor_emails_job()
                _assert_email_count('room_change_no_longer_eligible', 0)

                # Move course to an ineligible room.
                ineligible_room = 'Wheeler 150'
                _move_course(ineligible_room)
                _run_instructor_emails_job()
                _assert_email_count('room_change_no_longer_eligible', 1)

                # Move course back to its original location
                _move_course(original_room['location'])

                # Finally, let's pretend the course is scheduled to a room that was previously eligible.
                Scheduled.delete(section_id=section_id, term_id=term_id)
                _schedule(Room.find_room(ineligible_room).id)
                _run_instructor_emails_job()
                # Expect email.
                _assert_email_count('room_change_no_longer_eligible', 2)
                Scheduled.delete(section_id=section_id, term_id=term_id)


def _get_email_count(uid):
    return len(SentEmail.get_emails_sent_to(uid=uid))
