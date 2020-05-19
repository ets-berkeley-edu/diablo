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
from diablo import std_commit
from diablo.jobs.instructor_emails_job import InstructorEmailsJob
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.lib.util import utc_now
from diablo.models.course_preference import CoursePreference
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from sqlalchemy.orm.session import make_transient
from tests.util import test_approvals_workflow


class TestInstructorEmailsJob:

    def test_invite_new_instructors(self, app, db_session):
        """Invite all assigned instructors who haven't yet received an invitation."""
        term_id = app.config['CURRENT_TERM_ID']
        with test_approvals_workflow(app):
            # The job creates many new invitations.
            timestamp = utc_now()
            # Emails are queued but not sent.
            InstructorEmailsJob(app.app_context).run()
            assert len(_get_invitations_since(term_id, timestamp)) == 0
            # Emails are sent.
            QueuedEmailsJob(app.app_context).run()
            invitations = _get_invitations_since(term_id, timestamp)
            assert len(invitations) == 8

            # Each eligible course has an invitation.
            eligible_courses = SisSection.get_courses(term_id=term_id)
            assert len(eligible_courses) == 8
            for course in eligible_courses:
                sent_email = next((e for e in invitations if e.section_id == course['sectionId']), None)
                assert sent_email
                email_json = sent_email.to_api_json()
                assert len(email_json['recipientUids'])
                assert set(email_json['recipientUids']) == set([i['uid'] for i in course['instructors']])
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
            InstructorEmailsJob(app.app_context).run()
            QueuedEmailsJob(app.app_context).run()
            invitations = _get_invitations_since(term_id, timestamp)
            assert len(invitations) == 1
            invitation = invitations[0].to_api_json()
            assert invitation['sectionId'] == 50002
            assert invitation['recipientUids'] == ['10008']

    def test_course_opted_out(self, app):
        """Do not send email to courses that have opted out."""
        term_id = app.config['CURRENT_TERM_ID']
        with test_approvals_workflow(app):
            section_id = 50006
            CoursePreference.update_opt_out(term_id=term_id, section_id=section_id, opt_out=True)
            std_commit(allow_test_environment=True)

            timestamp = utc_now()
            # Emails are queued but not sent.
            InstructorEmailsJob(app.app_context).run()
            assert len(_get_invitations_since(term_id, timestamp)) == 0
            # Emails are sent.
            QueuedEmailsJob(app.app_context).run()
            invitations = _get_invitations_since(term_id, timestamp)
            assert len(invitations) == 8
            assert not next((e for e in invitations if e.section_id == section_id), None)


def _get_invitations_since(term_id, timestamp):
    return SentEmail.query\
        .filter_by(template_type='invitation', term_id=term_id)\
        .filter(SentEmail.sent_at >= timestamp)\
        .order_by(SentEmail.sent_at).all()
