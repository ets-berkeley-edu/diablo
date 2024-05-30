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
from diablo import db, std_commit
from diablo.jobs.emails_job import EmailsJob
from diablo.jobs.semester_start_job import SemesterStartJob
from diablo.lib.util import utc_now
from diablo.models.opt_out import OptOut
from diablo.models.queued_email import QueuedEmail
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy import text
from tests.util import simply_yield, test_scheduling_workflow


class TestSemesterStartJob:

    def test_semester_start(self):
        """Eligible courses are scheduled for recording by default at semester start."""
        with test_scheduling_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            instructor_uid = '10008'
            section_ids = ['50007', '50010']

            # Verify that nothing is scheduled
            assert Scheduled.get_all_scheduled(term_id=term_id) == []

            emails_to_instructor_count = len(SentEmail.get_emails_sent_to(instructor_uid))
            SemesterStartJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            for section_id in section_ids:
                scheduled = Scheduled.get_scheduled(section_id=section_id, term_id=term_id)
                assert instructor_uid in scheduled.instructor_uids

            # Verify one email sent to each instructor, even in the case of multiple eligible courses.
            emails_queued_for_instructor = [e for e in QueuedEmail.get_all(term_id=term_id) if e.recipient['uid'] == instructor_uid]
            assert len(emails_queued_for_instructor) == 1
            assert emails_queued_for_instructor[0].template_type == 'semester_start'
            assert emails_queued_for_instructor[0].message == "Well, then let's introduce ourselves. "\
                "I'm William Kinderman and these are my courses:\n"\
                'IND ENG 95: Richard Newton Lecture Series\n'\
                'MATH C51: Linear algebra and differential calculus'

            EmailsJob(simply_yield).run()
            emails_sent = SentEmail.get_emails_sent_to(instructor_uid)
            assert len(emails_sent) > emails_to_instructor_count
            email_sent = emails_sent[-1]
            assert email_sent.template_type == 'semester_start'
            assert email_sent.term_id == term_id

            """If recordings were already scheduled, send no additional email."""
            emails_to_instructor_count = len(SentEmail.get_emails_sent_to(instructor_uid))
            SemesterStartJob(simply_yield).run()
            assert len(SentEmail.get_emails_sent_to(instructor_uid)) == emails_to_instructor_count

    def test_course_opted_out(self, app):
        """Do not send email to courses that have opted out."""
        term_id = app.config['CURRENT_TERM_ID']
        with test_scheduling_workflow(app):
            instructor_uid = '10001'
            section_id = 50006
            OptOut.update_opt_out(instructor_uid=instructor_uid, term_id=term_id, section_id=section_id, opt_out=True)
            std_commit(allow_test_environment=True)

            timestamp = utc_now()
            # Emails are queued but not sent.
            SemesterStartJob(simply_yield).run()
            assert len(_get_announcements_since(term_id, timestamp)) == 0
            # Emails are sent.
            EmailsJob(simply_yield).run()
            announcements = _get_announcements_since(term_id, timestamp)
            assert len(announcements) == 14
            # Assert that cross-listings are accounted for in the 'sent_emails' table.
            _assert_coverage_of_cross_listings(
                expected_cross_listing_count=4,
                sent_emails=announcements,
                term_id=term_id,
            )
            assert not next((e for e in announcements if e.section_id == section_id), None)

    def test_no_duplicate_announcements(self, app):
        """Do not send the same announcement twice."""
        with test_scheduling_workflow(app):
            # First, get expected number of emails sent.
            term_id = app.config['CURRENT_TERM_ID']
            timestamp = utc_now()
            SemesterStartJob(simply_yield).run()
            EmailsJob(simply_yield).run()
            expected_count = len(_get_announcements_since(term_id, timestamp))

            # Clean up
            db.session.execute(text('DELETE FROM queued_emails; DELETE FROM sent_emails; DELETE FROM scheduled;'))

            # Next, run semester start twice before running queued_emails_task. Expect no duplicate emails.
            timestamp = utc_now()
            SemesterStartJob(simply_yield).run()
            SemesterStartJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            # Nothing is sent until we run the queued_emails_task.
            assert len(_get_announcements_since(term_id, timestamp)) == 0
            # Send queued emails.
            EmailsJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            assert len(_get_announcements_since(term_id, timestamp)) == expected_count
            # Verify no dupe emails.
            emails_sent = _get_announcements_since(term_id, timestamp)
            recipients = [f'{e.template_type}_{e.recipient_uid}_{e.term_id}_{e.section_id}' for e in emails_sent]
            assert len(set(recipients)) == len(recipients)


def _assert_coverage_of_cross_listings(expected_cross_listing_count, sent_emails, term_id):
    cross_listing_count = 0
    section_ids = [e.section_id for e in sent_emails]
    for course in SisSection.get_courses(section_ids=section_ids, term_id=term_id):
        for cross_listing in course['crossListings']:
            cross_listed_section_id = cross_listing['sectionId']
            announcement = next(
                (e for e in sent_emails if e.section_id == cross_listed_section_id and e.term_id == term_id), None)
            assert announcement
            cross_listing_count += 1
    assert cross_listing_count == expected_cross_listing_count


def _get_announcements_since(term_id, timestamp):
    return SentEmail.query\
        .filter_by(template_type='semester_start', term_id=term_id)\
        .filter(SentEmail.sent_at >= timestamp)\
        .order_by(SentEmail.sent_at).all()
