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
import json

from flask import current_app as app

from diablo import std_commit
from diablo.jobs.emails_job import EmailsJob
from diablo.jobs.remind_instructors_opted_out_job import RemindInstructorsOptedOutJob
from diablo.jobs.semester_start_job import SemesterStartJob
from diablo.models.queued_email import QueuedEmail
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from tests.util import simply_yield, test_scheduling_workflow


class TestRemindInstructorsOptedOutJob:

    def test_remind_instructors_opted_out(self):
        """Eligible, opted-out courses are not scheduled for recording but get reminder emails."""
        with test_scheduling_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            instructor_uid = '10008'
            solo_taught_section_id = '50007'
            co_taught_section_id = '50010'

            std_commit(allow_test_environment=True)

            emails_to_instructor_count = len(SentEmail.get_emails_sent_to(instructor_uid))
            SemesterStartJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            RemindInstructorsOptedOutJob(simply_yield).run()
            std_commit(allow_test_environment=True)

            for section_id in [solo_taught_section_id, co_taught_section_id]:
                assert not Scheduled.get_scheduled(section_id=section_id, term_id=term_id)

            # Verify one reminder sent to each instructor, even in the case of multiple eligible courses.
            reminders_queued_for_instructor = []
            for e in QueuedEmail.get_all(term_id=term_id):
                if e.recipient['uid'] == instructor_uid and e.template_type == 'remind_opted_out':
                    reminders_queued_for_instructor.append(e)

            assert len(reminders_queued_for_instructor) == 1
            assert reminders_queued_for_instructor[0].message == 'You are opted out, William Kinderman!\n'\
                'IND ENG 95, COL 001 | IND ENG 195, COL 001: Richard Newton Lecture Series,<br>\n'\
                'MATH C51, LEC 001 | STAT C51, LEC 003: Linear algebra and differential calculus'

            EmailsJob(simply_yield).run()
            emails_sent = SentEmail.get_emails_sent_to(instructor_uid)
            assert len(emails_sent) > emails_to_instructor_count
            email_sent = emails_sent[-1]
            assert email_sent.template_type == 'remind_opted_out'
            assert email_sent.term_id == term_id

    def test_opted_out_instructor_do_not_email(self, client, fake_auth):
        """No reminder emails go out if instructor has so requested."""
        with test_scheduling_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            instructor_uid = '10008'

            # Set do-not-email preference.
            fake_auth.login(instructor_uid)
            _api_update_do_not_email(client, uid=instructor_uid, do_not_email=True)
            std_commit(allow_test_environment=True)

            def _queued_email_count(instructor_uid):
                return len([e for e in QueuedEmail.get_all(term_id=term_id) if e.recipient['uid'] == instructor_uid])

            def _sent_email_count(instructor_uid):
                return len(SentEmail.get_emails_sent_to(instructor_uid))

            previously_sent_email_count = _sent_email_count(instructor_uid)
            SemesterStartJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            RemindInstructorsOptedOutJob(simply_yield).run()
            std_commit(allow_test_environment=True)

            # Verify no additional email sent to do-not-email instructors.
            assert _queued_email_count(instructor_uid) == 0
            EmailsJob(simply_yield).run()
            assert _sent_email_count(instructor_uid) == previously_sent_email_count

            # Remove do-not-email preference.
            _api_update_do_not_email(client, uid=instructor_uid, do_not_email=False)
            std_commit(allow_test_environment=True)


def _api_update_do_not_email(client, uid, do_not_email, expected_status_code=200):
    response = client.post(
        f'/api/user/{uid}/do_not_email/update',
        data=json.dumps({'doNotEmail': do_not_email}),
        content_type='application/json',
    )
    assert response.status_code == expected_status_code
    return response.json
