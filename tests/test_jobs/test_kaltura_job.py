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
from diablo.jobs.kaltura_job import KalturaJob
from diablo.models.approval import Approval
from diablo.models.room import Room
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.util import test_approvals_workflow


class TestKalturaJob:

    def test_scheduling_of_recordings(self):
        """If a course is scheduled for recording then email is sent to its instructor(s)."""
        with test_approvals_workflow(app):
            section_id = 22287
            term_id = app.config['CURRENT_TERM_ID']
            email_template_type = 'recordings_scheduled'

            def _get_emails_sent():
                return SentEmail.get_emails_of_type(
                    section_id=section_id,
                    template_type=email_template_type,
                    term_id=term_id,
                )

            emails_sent = _get_emails_sent()
            KalturaJob(app.app_context).run()
            std_commit(allow_test_environment=True)
            # Expect no emails sent during action above
            assert _get_emails_sent() == emails_sent

            course = SisSection.get_course(section_id=section_id, term_id=term_id)
            instructors = course['instructors']
            assert len(instructors) == 2
            room_id = Room.find_room(course['meetingLocation']).id

            # This course requires two (2) approvals.
            approvals = [
                Approval.create(
                    approved_by_uid=instructors[0]['uid'],
                    term_id=term_id,
                    section_id=section_id,
                    approver_type_='instructor',
                    publish_type_='canvas',
                    recording_type_='presentation_audio',
                    room_id=Room.find_room('Barker 101').id,
                ),
            ]
            """If we have insufficient approvals then do nothing."""
            email_count = _get_emails_sent()
            KalturaJob(app.app_context).run()
            std_commit(allow_test_environment=True)
            assert _get_emails_sent() == email_count

            # The second approval
            approvals.append(
                Approval.create(
                    approved_by_uid=instructors[1]['uid'],
                    term_id=term_id,
                    section_id=section_id,
                    approver_type_='instructor',
                    publish_type_='kaltura_media_gallery',
                    recording_type_='presenter_presentation_audio',
                    room_id=room_id,
                ),
            )

            """If a course is scheduled for recording then email is sent to its instructor(s)."""
            email_count = len(_get_emails_sent())
            KalturaJob(app.app_context).run()
            std_commit(allow_test_environment=True)
            emails_sent = _get_emails_sent()
            assert len(emails_sent) == email_count + 1
            email_sent = emails_sent[-1].to_api_json()
            assert set(email_sent['recipientUids']) == {'98765', '87654'}
            assert email_sent['sectionId'] == section_id
            assert email_sent['templateType'] == 'recordings_scheduled'
            assert email_sent['termId'] == term_id
            assert email_sent['sentAt']

            """If recordings were already scheduled then do nothing, send no email."""
            email_count = len(_get_emails_sent())
            KalturaJob(app.app_context).run()
            assert len(_get_emails_sent()) == email_count
