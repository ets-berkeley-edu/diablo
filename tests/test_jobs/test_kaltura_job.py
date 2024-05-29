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
import random

from diablo import db, std_commit
from diablo.jobs.emails_job import EmailsJob
from diablo.jobs.kaltura_job import KalturaJob
from diablo.jobs.schedule_updates_job import ScheduleUpdatesJob
from diablo.lib.berkeley import are_scheduled_dates_obsolete, are_scheduled_times_obsolete, get_recording_end_date, \
    get_recording_start_date
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy import text
from tests.test_api.api_test_utils import api_get_course, get_eligible_meeting, get_instructor_uids, mock_scheduled
from tests.util import override_config, simply_yield, test_approvals_workflow


admin_uid = '90001'
deleted_section_id = 50018


class TestKalturaJob:

    def test_new_course_scheduled(self, client):
        """New courses are scheduled for recording by default."""
        with test_approvals_workflow(app):
            section_id = 50012
            term_id = app.config['CURRENT_TERM_ID']
            course = SisSection.get_course(section_id=section_id, term_id=term_id)
            instructors = course['instructors']
            assert len(instructors) == 2

            # Verify that course is not scheduled
            assert Scheduled.get_scheduled(section_id=section_id, term_id=term_id) is None

            def _get_emails_sent():
                return SentEmail.get_emails_of_type(
                    section_ids=[section_id],
                    template_type='new_class_scheduled',
                    term_id=term_id,
                )

            """If a course is scheduled for recording then email is sent to its instructor(s)."""
            email_count = len(_get_emails_sent())
            KalturaJob(simply_yield).run()
            std_commit(allow_test_environment=True)
            assert Scheduled.get_scheduled(section_id=section_id, term_id=term_id)

            # Verify emails sent
            EmailsJob(simply_yield).run()
            emails_sent = _get_emails_sent()
            assert len(emails_sent) == email_count + 2
            assert [emails_sent[-1].recipient_uid, emails_sent[-2].recipient_uid] == ['10009', '10010']
            email_sent = emails_sent[-1]
            assert email_sent.section_id == section_id
            assert email_sent.template_type == 'new_class_scheduled'
            assert email_sent.term_id == term_id

            """If recordings were already scheduled then do nothing, send no email."""
            email_count = len(_get_emails_sent())
            KalturaJob(simply_yield).run()
            assert len(_get_emails_sent()) == email_count

    def test_canceled_course(self, db_session):
        term_id = app.config['CURRENT_TERM_ID']
        with test_approvals_workflow(app):
            course = SisSection.get_course(section_id=deleted_section_id, term_id=term_id, include_deleted=True)
            room = course.get('meetings', {}).get('eligible', [])[0]['room']
            _schedule(room['id'], deleted_section_id)
            _run_jobs()
            _assert_email_count(1, deleted_section_id, 'no_longer_scheduled')

    def test_room_change(self, db_session, client, fake_auth):
        section_id = 50004
        term_id = app.config['CURRENT_TERM_ID']

        def _move_course(meeting_location):
            db.session.execute(
                text('UPDATE sis_sections SET meeting_location = :meeting_location WHERE term_id = :term_id AND section_id = :section_id'),
                {
                    'meeting_location': meeting_location,
                    'section_id': section_id,
                    'term_id': term_id,
                },
            )
        with test_approvals_workflow(app):
            course = SisSection.get_course(section_id=section_id, term_id=term_id)
            eligible_meetings = course.get('meetings', {}).get('eligible', [])
            assert len(eligible_meetings) == 1
            original_room = eligible_meetings[0]['room']
            assert original_room['location'] == 'Li Ka Shing 145'

            # Schedule
            _schedule(original_room['id'], section_id)
            _run_jobs()
            _assert_email_count(0, section_id, 'room_change')
            _assert_email_count(0, section_id, 'room_change_no_longer_eligible')

            # Move course to some other eligible room.
            _move_course('Barker 101')
            _run_jobs()
            _assert_email_count(1, section_id, 'room_change')
            _assert_email_count(0, section_id, 'room_change_no_longer_eligible')

            # Move course to an ineligible room.
            ineligible_room = 'Wheeler 150'
            _move_course(ineligible_room)
            _run_jobs()
            _assert_email_count(1, section_id, 'room_change')
            _assert_email_count(1, section_id, 'room_change_no_longer_eligible')

            # Move course back to its original location
            _move_course(original_room['location'])

            # Finally, let's pretend the course was previously scheduled to an ineligible room.
            Scheduled.delete(section_id=section_id, term_id=term_id)
            _schedule(Room.find_room(ineligible_room).id, section_id)
            _run_jobs()
            # Expect email.
            _assert_email_count(2, section_id, 'room_change')
            _assert_email_count(1, section_id, 'room_change_no_longer_eligible')
            Scheduled.delete(section_id=section_id, term_id=term_id)

            fake_auth.login(admin_uid)
            course = api_get_course(client, term_id, section_id)
            assert len(course['updateHistory']) == 3

            assert course['updateHistory'][0]['fieldName'] == 'meeting_updated'
            assert course['updateHistory'][0]['fieldValueOld']['room']['location'] == 'Li Ka Shing 145'
            assert course['updateHistory'][0]['fieldValueOld']['room']['kalturaResourceId']
            assert course['updateHistory'][0]['fieldValueNew']['room']['location'] == 'Barker 101'
            assert course['updateHistory'][0]['fieldValueNew']['room']['kalturaResourceId']
            assert course['updateHistory'][0]['requestedByName'] is None
            assert course['updateHistory'][0]['requestedByUid'] is None
            assert course['updateHistory'][0]['status'] == 'succeeded'

            assert course['updateHistory'][1]['fieldName'] == 'room_not_eligible'
            assert course['updateHistory'][1]['fieldValueOld']['location'] == 'Barker 101'
            assert course['updateHistory'][1]['fieldValueOld']['kalturaResourceId']
            assert course['updateHistory'][1]['fieldValueNew']['location'] == 'Wheeler 150'
            assert course['updateHistory'][1]['fieldValueNew']['kalturaResourceId'] is None
            assert course['updateHistory'][1]['requestedByName'] is None
            assert course['updateHistory'][1]['requestedByUid'] is None
            assert course['updateHistory'][1]['status'] == 'succeeded'

            assert course['updateHistory'][2]['fieldName'] == 'meeting_updated'
            assert course['updateHistory'][2]['fieldValueOld']['room']['location'] == 'Wheeler 150'
            assert course['updateHistory'][2]['fieldValueOld']['room']['kalturaResourceId'] is None
            assert course['updateHistory'][2]['fieldValueNew']['room']['location'] == 'Li Ka Shing 145'
            assert course['updateHistory'][2]['fieldValueNew']['room']['kalturaResourceId']
            assert course['updateHistory'][2]['requestedByName'] is None
            assert course['updateHistory'][2]['requestedByUid'] is None
            assert course['updateHistory'][2]['status'] == 'succeeded'

    def test_datetime_change(self, db_session, client, fake_auth):
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50004
        meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    def _schedule():
                        mock_scheduled(
                            meeting=meeting,
                            override_end_time='16:59',
                            override_start_time='08:00',
                            section_id=section_id,
                            term_id=term_id,
                        )
                        course = SisSection.get_course(section_id=section_id, term_id=term_id)
                        for scheduled in course['scheduled']:
                            assert are_scheduled_dates_obsolete(meeting=meeting, scheduled=scheduled) is False
                            assert are_scheduled_times_obsolete(meeting=meeting, scheduled=scheduled) is True

                    # First time scheduled.
                    _schedule()
                    _run_jobs()
                    _assert_email_count(1, section_id, 'room_change')

                    # Unschedule and schedule a second time.
                    Scheduled.delete(section_id=section_id, term_id=term_id)
                    _schedule()

                    _run_jobs()
                    # Another notification is emailed because it is a new schedule.
                    _assert_email_count(2, section_id, 'room_change')

                    # Run jobs again and expect no alerts.
                    _run_jobs()
                    _assert_email_count(2, section_id, 'room_change')

                    fake_auth.login(admin_uid)
                    course = api_get_course(client, term_id, section_id)
                    assert len(course['updateHistory']) == 2
                    for u in course['updateHistory']:
                        assert u['fieldName'] == 'meeting_updated'
                        assert u['fieldValueOld'] == {
                            'days': 'MOWE',
                            'startTime': '08:00',
                            'endTime': '16:59',
                            'startDate': '2024-05-29',
                            'endDate': '2021-12-08',
                        }
                        assert u['fieldValueNew'] == {
                            'days': 'MOWE',
                            'startTime': '13:00',
                            'endTime': '13:59',
                            'startDate': '2024-05-29',
                            'endDate': '2021-12-08',
                        }
                        assert u['requestedByName'] is None
                        assert u['requestedByUid'] is None
                        assert u['status'] == 'succeeded'

    def test_instructor_added(self, client, fake_auth):
        """Emails new instructor when added to scheduled course."""
        with test_approvals_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            section_id = 50005
            room_id = Room.find_room('Barker 101').id
            # The course has two instructors.
            instructor_1_uid, instructor_2_uid = get_instructor_uids(section_id=section_id, term_id=term_id)
            # Uh oh! Only one of them has been scheduled.
            meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
            Scheduled.create(
                course_display_name=f'term_id:{term_id} section_id:{section_id}',
                instructor_uids=[instructor_1_uid],
                collaborator_uids=[],
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                meeting_start_time=meeting['startTime'],
                publish_type_='kaltura_media_gallery',
                recording_type_='presenter_presentation_audio',
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )

            # Message queued but not sent.
            ScheduleUpdatesJob(simply_yield).run()
            KalturaJob(simply_yield).run()
            _assert_email_count(0, section_id, 'instructors_added')

            EmailsJob(simply_yield).run()
            _assert_email_count(1, section_id, 'instructors_added')

            fake_auth.login(admin_uid)
            course = api_get_course(client, term_id, section_id)
            assert len(course['updateHistory']) == 1
            assert course['updateHistory'][0]['fieldName'] == 'instructor_uids'
            assert course['updateHistory'][0]['fieldValueOld'] == ['10006']
            assert course['updateHistory'][0]['fieldValueNew'] == ['10006', '10007']
            assert course['updateHistory'][0]['requestedByName'] is None
            assert course['updateHistory'][0]['requestedByUid'] is None
            assert course['updateHistory'][0]['status'] == 'succeeded'

    def test_instructor_removed(self, client, fake_auth):
        """Emails instructor when removed from scheduled course."""
        with test_approvals_workflow(app):
            term_id = app.config['CURRENT_TERM_ID']
            section_id = 50005
            room_id = Room.find_room('Barker 101').id
            # The course has two instructors.
            instructor_1_uid, instructor_2_uid = get_instructor_uids(section_id=section_id, term_id=term_id)
            # Uh oh! A third instructor somehow got scheduled.
            instructor_3_uid = '10010'
            meeting = get_eligible_meeting(section_id=section_id, term_id=term_id)
            Scheduled.create(
                course_display_name=f'term_id:{term_id} section_id:{section_id}',
                instructor_uids=[instructor_1_uid, instructor_2_uid, instructor_3_uid],
                collaborator_uids=[],
                kaltura_schedule_id=random.randint(1, 10),
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                meeting_start_time=meeting['startTime'],
                publish_type_='kaltura_media_gallery',
                recording_type_='presenter_presentation_audio',
                room_id=room_id,
                section_id=section_id,
                term_id=term_id,
            )

            # Message queued but not sent.
            ScheduleUpdatesJob(simply_yield).run()
            KalturaJob(simply_yield).run()
            _assert_email_count(0, section_id, 'instructors_removed')

            EmailsJob(simply_yield).run()
            _assert_email_count(1, section_id, 'instructors_removed')

            fake_auth.login(admin_uid)
            course = api_get_course(client, term_id, section_id)
            assert len(course['updateHistory']) == 1
            assert course['updateHistory'][0]['fieldName'] == 'instructor_uids'
            assert course['updateHistory'][0]['fieldValueOld'] == ['10006', '10007', '10010']
            assert course['updateHistory'][0]['fieldValueNew'] == ['10006', '10007']
            assert course['updateHistory'][0]['requestedByName'] is None
            assert course['updateHistory'][0]['requestedByUid'] is None
            assert course['updateHistory'][0]['status'] == 'succeeded'


def _assert_email_count(expected_count, section_id, template_type):
    term_id = app.config['CURRENT_TERM_ID']
    emails_sent = SentEmail.get_emails_of_type(
        section_ids=[section_id],
        template_type=template_type,
        term_id=term_id,
    )
    assert len(emails_sent) == expected_count


def _get_email_count(uid):
    return len(SentEmail.get_emails_sent_to(uid=uid))


def _run_jobs():
    ScheduleUpdatesJob(simply_yield).run()
    KalturaJob(simply_yield).run()
    EmailsJob(simply_yield).run()


def _schedule(room_id, section_id):
    term_id = app.config['CURRENT_TERM_ID']
    mock_scheduled(
        override_room_id=room_id,
        section_id=section_id,
        term_id=term_id,
    )
