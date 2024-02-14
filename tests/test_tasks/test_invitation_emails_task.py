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
from diablo.jobs.tasks.invitation_emails_task import InvitationEmailsTask
from diablo.jobs.tasks.queued_emails_task import QueuedEmailsTask
from diablo.lib.util import utc_now
from diablo.models.course_preference import CoursePreference
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from sqlalchemy import text
from sqlalchemy.orm.session import make_transient
from tests.util import test_approvals_workflow


class TestInvitationEmailsTask:

    def test_course_opted_out(self, app):
        """Do not send email to courses that have opted out."""
        term_id = app.config['CURRENT_TERM_ID']
        with test_approvals_workflow(app):
            section_id = 50006
            CoursePreference.update_opt_out(term_id=term_id, section_id=section_id, opt_out=True)
            std_commit(allow_test_environment=True)

            timestamp = utc_now()
            # Emails are queued but not sent.
            InvitationEmailsTask().run()
            assert len(_get_invitations_since(term_id, timestamp)) == 0
            # Emails are sent.
            QueuedEmailsTask().run()
            invitations = _get_invitations_since(term_id, timestamp)
            assert len(invitations) == 18
            # Assert that cross-listings are accounted for in the 'sent_emails' table.
            _assert_coverage_of_cross_listings(
                expected_cross_listing_count=4,
                sent_emails=invitations,
                term_id=term_id,
            )
            assert not next((e for e in invitations if e.section_id == section_id), None)

    def test_invite_new_instructors(self, app, db_session):
        """Invite all assigned instructors who haven't yet received an invitation."""
        term_id = app.config['CURRENT_TERM_ID']
        with test_approvals_workflow(app):
            # The job creates many new invitations.
            timestamp = utc_now()
            # Emails are queued but not sent.
            InvitationEmailsTask().run()
            assert len(_get_invitations_since(term_id, timestamp)) == 0
            # Emails are sent. We have more emails than courses since some courses have multiple instructors.
            QueuedEmailsTask().run()
            invitations = _get_invitations_since(term_id, timestamp)
            assert len(invitations) == 18
            # Assert that cross-listings are accounted for in the 'sent_emails' table.
            _assert_coverage_of_cross_listings(
                expected_cross_listing_count=4,
                sent_emails=invitations,
                term_id=term_id,
            )
            # Each eligible course has an invitation.
            eligible_courses = [c for c in SisSection.get_courses(term_id=term_id) if len(c['meetings']['eligible']) == 1]
            assert len(eligible_courses) == 11
            for course in eligible_courses:
                for i in course['instructors']:
                    sent_email = next((e for e in invitations if e.section_id == course['sectionId'] and i['uid'] == e.recipient_uid), None)
                    assert sent_email
                    email_json = sent_email.to_api_json()
                    assert email_json['recipientUid'] == i['uid']
                    assert email_json['sectionId'] == course['sectionId']
                    assert email_json['templateType'] == 'invitation'
                    assert email_json['termId'] == term_id
                    assert email_json['sentAt']

            # Add an instructor.
            section = SisSection.query.filter_by(term_id=term_id, section_id=50002).first()
            db_session.expunge(section)
            make_transient(section)
            section.id = None
            section.instructor_uid = '10008'
            db_session.add(section)
            std_commit(allow_test_environment=True)

            # Re-run the job. An email is sent to the new instructor only.
            timestamp = utc_now()
            InvitationEmailsTask().run()
            QueuedEmailsTask().run()
            invitations = _get_invitations_since(term_id, timestamp)
            assert len(invitations) == 1
            invitation = invitations[0].to_api_json()
            assert invitation['sectionId'] == 50002
            assert invitation['recipientUid'] == '10008'

    def test_no_duplicate_invites(self, app):
        """Do not send the same invite twice."""
        with test_approvals_workflow(app):
            # First, get expected number of emails sent.
            term_id = app.config['CURRENT_TERM_ID']
            timestamp = utc_now()
            InvitationEmailsTask().run()
            QueuedEmailsTask().run()
            expected_count = len(_get_invitations_since(term_id, timestamp))

            # Clean up
            db.session.execute(text('DELETE FROM queued_emails; DELETE FROM sent_emails;'))

            # Next, run invitation_task twice before running queued_emails_task. Expect no duplicate emails.
            timestamp = utc_now()
            InvitationEmailsTask().run()
            InvitationEmailsTask().run()
            std_commit(allow_test_environment=True)
            # Nothing is sent until we run the queued_emails_task.
            assert len(_get_invitations_since(term_id, timestamp)) == 0
            # Send queued emails.
            QueuedEmailsTask().run()
            std_commit(allow_test_environment=True)
            assert len(_get_invitations_since(term_id, timestamp)) == expected_count
            # Verify no dupe emails.
            emails_sent = _get_invitations_since(term_id, timestamp)
            recipients = [f'{e.template_type}_{e.recipient_uid}_{e.term_id}_{e.section_id}' for e in emails_sent]
            assert len(set(recipients)) == len(recipients)


def _assert_coverage_of_cross_listings(expected_cross_listing_count, sent_emails, term_id):
    cross_listing_count = 0
    section_ids = [e.section_id for e in sent_emails]
    for course in SisSection.get_courses(section_ids=section_ids, term_id=term_id):
        for cross_listing in course['crossListings']:
            cross_listed_section_id = cross_listing['sectionId']
            invitation = next(
                (e for e in sent_emails if e.section_id == cross_listed_section_id and e.term_id == term_id), None)
            assert invitation
            cross_listing_count += 1
    assert cross_listing_count == expected_cross_listing_count


def _get_invitations_since(term_id, timestamp):
    return SentEmail.query\
        .filter_by(template_type='invitation', term_id=term_id)\
        .filter(SentEmail.sent_at >= timestamp)\
        .order_by(SentEmail.sent_at).all()
