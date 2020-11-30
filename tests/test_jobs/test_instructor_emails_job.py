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
        with enabled_job(job_key=InstructorEmailsJob.key()):
            term_id = app.config['CURRENT_TERM_ID']
            section_id = 50004
            with test_approvals_workflow(app):
                def _run_jobs():
                    InstructorEmailsJob(simply_yield).run()
                    QueuedEmailsJob(simply_yield).run()

                def _schedule():
                    mock_scheduled(
                        override_room_id=Room.find_room('Barker 101').id,
                        section_id=section_id,
                        term_id=term_id,
                    )
                    course = SisSection.get_course(section_id=section_id, term_id=term_id)
                    assert course['scheduled']['hasObsoleteRoom'] is True

                def _assert_alert_count(count):
                    emails_sent = SentEmail.get_emails_of_type(
                        section_ids=[section_id],
                        template_type='room_change_no_longer_eligible',
                        term_id=term_id,
                    )
                    assert len(emails_sent) == count

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


def _get_email_count(uid):
    return len(SentEmail.get_emails_sent_to(uid=uid))
