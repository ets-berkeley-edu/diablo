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
from datetime import datetime, timedelta
import random

from diablo import db, std_commit
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date, scheduled_dates_are_obsolete
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy import text
from tests.test_api.api_test_utils import get_instructor_uids
from tests.util import override_config, test_approvals_workflow


class TestRecordingDates:

    def test_recording_end_date(self):
        capture_recordings_until = '2525-11-25'
        with override_config(app, 'CURRENT_TERM_RECORDINGS_END', capture_recordings_until):
            meeting = {'endDate': '2525-12-11 00:00:00 UTC'}
            assert get_recording_end_date(meeting) == _to_datetime(capture_recordings_until)

            meeting = {'endDate': '2525-11-01 00:00:00 UTC'}
            assert get_recording_end_date(meeting) == _to_datetime('2525-11-01')

    def test_recording_start_date(self):
        term_begin = '2525-09-07'
        with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', term_begin):
            meeting = {'startDate': '2525-08-26 00:00:00 UTC'}
            assert get_recording_start_date(meeting) == _to_datetime(term_begin)

            meeting = {'startDate': '2525-09-14 00:00:00 UTC'}
            assert get_recording_start_date(meeting) == _to_datetime('2525-09-14')

    def test_start_date_is_in_the_past(self):
        df = '%Y-%m-%d'
        today = datetime.today()
        term_begin = today - timedelta(days=7)
        first_meeting = today - timedelta(days=3)
        with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', datetime.strftime(term_begin, df)):
            meeting = {'startDate': f'{datetime.strftime(first_meeting, df)} 00:00:00 UTC'}
            start_date = get_recording_start_date(meeting, return_today_if_past_start=True)
            assert datetime.strftime(start_date, df) == datetime.strftime(today, df)


class TestObsoleteScheduledDates:

    @property
    def section_id(self):
        return 50000

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def _schedule_recordings(self, meeting, override_start_date=None, override_end_date=None):
        scheduled = Scheduled.create(
            instructor_uids=get_instructor_uids(term_id=self.term_id, section_id=self.section_id),
            kaltura_schedule_id=random.randint(1, 10),
            meeting_days='MO,WE,FR',
            meeting_end_date=override_end_date or get_recording_end_date(meeting),
            meeting_end_time='10:59',
            meeting_start_date=override_start_date or get_recording_start_date(meeting, return_today_if_past_start=True),
            meeting_start_time='10:00',
            publish_type_='kaltura_media_gallery',
            recording_type_='presenter_presentation_audio',
            room_id=Room.get_room_id(section_id=self.section_id, term_id=self.term_id),
            section_id=self.section_id,
            term_id=self.term_id,
        )
        if override_start_date or override_end_date:
            sql = 'UPDATE scheduled SET'
            sql += ' meeting_end_date = :meeting_end_date' if override_end_date else ''
            sql += ' meeting_start_date = :meeting_start_date' if override_start_date else ''
            sql += ' WHERE id = :id'
            db.session.execute(
                text(sql),
                {
                    'id': scheduled.id,
                    'meeting_end_date': override_end_date,
                    'meeting_start_date': override_start_date,
                },
            )
        std_commit(allow_test_environment=True)

    def test_scheduled_before_the_meeting_start(self):
        meeting = {
            'endDate': '2525-12-11',
            'startDate': '2525-08-25',
        }
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    self._schedule_recordings(meeting)
                    course = SisSection.get_course(section_id=self.section_id, term_id=self.term_id)
                    assert scheduled_dates_are_obsolete(meeting=meeting, scheduled=course['scheduled']) is False

    def test_scheduled_after_the_meeting_start(self):
        meeting = {
            'endDate': _format(datetime.now() + timedelta(days=100)),
            'startDate': _format(datetime.now() - timedelta(days=100)),
        }
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    self._schedule_recordings(meeting)
                    course = SisSection.get_course(section_id=self.section_id, term_id=self.term_id)
                    assert scheduled_dates_are_obsolete(meeting=meeting, scheduled=course['scheduled']) is False

    def test_scheduled_obsolete_start_date(self):
        meeting = {
            'endDate': '2525-12-11',
            'startDate': '2525-08-25',
        }
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    self._schedule_recordings(meeting=meeting, override_start_date='2525-08-01')
                    course = SisSection.get_course(section_id=self.section_id, term_id=self.term_id)
                    assert scheduled_dates_are_obsolete(meeting=meeting, scheduled=course['scheduled']) is True

    def test_scheduled_obsolete_end_date(self):
        meeting = {
            'endDate': '2525-12-11',
            'startDate': '2525-08-25',
        }
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    self._schedule_recordings(meeting=meeting, override_end_date='2525-12-01')
                    course = SisSection.get_course(section_id=self.section_id, term_id=self.term_id)
                    assert scheduled_dates_are_obsolete(meeting=meeting, scheduled=course['scheduled']) is True


def _format(date):
    return datetime.strftime(date, '%Y-%m-%d')


def _to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d')
