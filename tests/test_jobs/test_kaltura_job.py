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
from diablo import std_commit
from diablo.jobs.kaltura_job import KalturaJob
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.models.approval import Approval
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.util import simply_yield, test_approvals_workflow

admin_uid = '90001'


class TestKalturaJob:

    def test_cross_listed_course(self):
        """Recordings will be scheduled if and only if all instructor(s) approve."""
        with test_approvals_workflow(app):
            section_id = 50012
            term_id = app.config['CURRENT_TERM_ID']
            email_template_type = 'recordings_scheduled'

            def _get_emails_sent():
                return SentEmail.get_emails_of_type(
                    section_ids=[section_id],
                    template_type=email_template_type,
                    term_id=term_id,
                )

            emails_sent = _get_emails_sent()
            KalturaJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            # Expect no emails sent during action above
            assert _get_emails_sent() == emails_sent

            course = SisSection.get_course(section_id=section_id, term_id=term_id)
            instructors = course['instructors']
            cross_listings = course['crossListings']
            room_id = Room.find_room(course['meetings']['eligible'][0]['location']).id

            assert len(instructors) == 2
            assert room_id == Room.find_room("O'Brien 212").id
            assert len(cross_listings) == 1
            assert len(course['canvasCourseSites']) == 2

            # This course requires two (2) approvals.
            approvals = [
                Approval.create(
                    approved_by_uid=instructors[0]['uid'],
                    approver_type_='instructor',
                    publish_type_='kaltura_my_media',
                    recording_type_='presentation_audio',
                    room_id=room_id,
                    section_id=section_id,
                    term_id=term_id,
                ),
            ]
            """If we have insufficient approvals then do nothing."""
            email_count = _get_emails_sent()
            KalturaJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            assert _get_emails_sent() == email_count

            # The second approval
            final_approval = Approval.create(
                approved_by_uid=instructors[1]['uid'],
                approver_type_='instructor',
                publish_type_='kaltura_media_gallery',
                recording_type_='presenter_presentation_audio',
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )
            approvals.append(final_approval)

            """If a course is scheduled for recording then email is sent to its instructor(s)."""
            email_count = len(_get_emails_sent())
            KalturaJob(simply_yield).run()
            std_commit(allow_test_environment=True)

            # Verify publish and recording types
            scheduled = Scheduled.get_scheduled(term_id=term_id, section_id=section_id)
            assert scheduled.publish_type == final_approval.publish_type
            assert scheduled.recording_type == final_approval.recording_type
            assert scheduled.section_id == section_id
            assert scheduled.term_id == term_id

            # Verify emails sent
            QueuedEmailsJob(app.app_context).run()
            emails_sent = _get_emails_sent()
            assert len(emails_sent) == email_count + 2
            assert [emails_sent[-1].recipient_uid, emails_sent[-2].recipient_uid] == ['10009', '10010']
            email_sent = emails_sent[-1]
            assert email_sent.section_id == section_id
            assert email_sent.template_type == 'recordings_scheduled'
            assert email_sent.term_id == term_id

            """If recordings were already scheduled then do nothing, send no email."""
            email_count = len(_get_emails_sent())
            KalturaJob(simply_yield).run()
            assert len(_get_emails_sent()) == email_count

    def test_admin_approval(self):
        """Course is scheduled for recording if an admin user has approved."""
        with test_approvals_workflow(app):
            section_id = 50005
            term_id = app.config['CURRENT_TERM_ID']
            course = SisSection.get_course(section_id=section_id, term_id=term_id)
            instructors = course['instructors']
            assert len(instructors) == 2

            # Verify that course is not scheduled
            assert Scheduled.get_scheduled(section_id=section_id, term_id=term_id) is None

            Approval.create(
                approved_by_uid=admin_uid,
                approver_type_='admin',
                publish_type_='kaltura_my_media',
                recording_type_='presentation_audio',
                room_id=Room.find_room('Barker 101').id,
                section_id=section_id,
                term_id=term_id,
            )
            KalturaJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            # Admin approval is all we need.
            assert Scheduled.get_scheduled(section_id=section_id, term_id=term_id)
