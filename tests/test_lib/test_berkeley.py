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
from diablo.lib.berkeley import DAYS, get_first_matching_datetime_of_term, get_recording_end_date, \
    get_recording_start_date, is_schedule_obsolete
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app
import pytz
from sqlalchemy import text
from tests.test_api.api_test_utils import get_instructor_uids
from tests.util import override_config, test_approvals_workflow


class TestRecordingDates:

    def test_recording_end_date(self):
        # End date is a Friday
        recordings_end_date = '2525-11-23'
        with override_config(app, 'CURRENT_TERM_RECORDINGS_END', recordings_end_date):
            meeting = {
                'days': 'TUTH',
                'endDate': '2525-12-11 00:00:00 UTC',
            }
            # Expect preceding Thursday
            assert get_recording_end_date(meeting) == _to_datetime('2525-11-22')

            meeting = {
                'days': 'MO',
                # End date is a Thursday
                'endDate': '2525-11-01 00:00:00 UTC',
            }
            # Expect preceding Monday
            assert get_recording_end_date(meeting) == _to_datetime('2525-10-29')

    def test_recording_end_date_with_offset(self):
        recordings_end_date = '2020-11-24'
        with override_config(app, 'CURRENT_TERM_RECORDINGS_END', recordings_end_date):
            meeting = {
                'days': 'MO',
                'endDate': '2020-12-11 00:00:00 UTC',
            }
            # The last recording is on a Monday.
            assert get_recording_end_date(meeting) == _to_datetime('2020-11-23')

    def test_recording_start_date(self):
        # Begin date is a Friday
        recordings_begin_date = '2525-09-07'
        with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', recordings_begin_date):
            meeting = {
                'days': 'MO',
                'startDate': '2525-08-26 00:00:00 UTC',
            }
            # Expect the following Monday
            assert get_recording_start_date(meeting) == _to_datetime('2525-09-10')

            meeting = {
                'days': 'FR',
                'startDate': '2525-09-14 00:00:00 UTC',
            }
            assert get_recording_start_date(meeting) == _to_datetime('2525-09-14')

    def test_start_date_is_in_the_past(self):
        df = '%Y-%m-%d'
        today = datetime.today()
        recordings_begin_date = today - timedelta(days=7)
        first_meeting = today - timedelta(days=3)
        with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', datetime.strftime(recordings_begin_date, df)):
            meeting = {
                'days': ''.join(DAYS),
                'startDate': f'{datetime.strftime(first_meeting, df)} 00:00:00 UTC',
            }
            start_date = get_recording_start_date(meeting, return_today_if_past_start=True)
            assert datetime.strftime(start_date, df) == datetime.strftime(today, df)


class TestObsoleteScheduledDates:

    @property
    def section_id(self):
        return 50000

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_scheduled_before_the_meeting_start(self):
        meeting = {
            'days': ''.join(DAYS),
            'endDate': '2525-12-11',
            'endTime': '10:59',
            'startDate': '2525-08-25',
            'startTime': '10:00',
        }
        self._assert_schedule_is_obsolete(expected_result=False, meeting=meeting)

    def test_scheduled_after_the_meeting_start(self):
        meeting = {
            'days': ''.join(DAYS),
            'endDate': _format(datetime.now() + timedelta(days=100)),
            'endTime': '10:59',
            'startDate': _format(datetime.now() - timedelta(days=100)),
            'startTime': '10:00',
        }
        self._assert_schedule_is_obsolete(expected_result=False, meeting=meeting)

    def test_scheduled_obsolete_start_date(self):
        meeting = {
            'days': ''.join(DAYS),
            'endDate': '2525-12-11',
            'endTime': '10:59',
            'startDate': '2525-08-25',
            'startTime': '10:00',
        }
        self._assert_schedule_is_obsolete(expected_result=True, meeting=meeting, override_start_date='2525-08-01')

    def test_scheduled_obsolete_end_date(self):
        meeting = {
            'days': ''.join(DAYS),
            'endDate': '2525-12-11',
            'endTime': '10:59',
            'startDate': '2525-08-25',
            'startTime': '10:00',
        }
        self._assert_schedule_is_obsolete(expected_result=True, meeting=meeting, override_end_date='2525-12-01')

    def test_scheduled_obsolete_times(self):
        meeting = {
            'days': ''.join(DAYS),
            'endDate': '2525-12-11',
            'endTime': '10:59',
            'startDate': '2525-08-25',
            'startTime': '10:00',
        }
        self._assert_schedule_is_obsolete(
            expected_result=True,
            meeting=meeting,
            override_end_time='14:00',
            override_start_time='14:59',
        )

    def _assert_schedule_is_obsolete(
            self,
            expected_result,
            meeting,
            override_end_date=None,
            override_end_time=None,
            override_start_date=None,
            override_start_time=None,
    ):
        with test_approvals_workflow(app):
            with override_config(app, 'CURRENT_TERM_RECORDINGS_BEGIN', meeting['startDate']):
                with override_config(app, 'CURRENT_TERM_RECORDINGS_END', meeting['endDate']):
                    self._schedule_recordings(
                        meeting=meeting,
                        override_end_date=override_end_date,
                        override_end_time=override_end_time,
                        override_start_date=override_start_date,
                        override_start_time=override_start_time,
                    )
                    course = SisSection.get_course(section_id=self.section_id, term_id=self.term_id)
                    assert is_schedule_obsolete(meeting=meeting, scheduled=course['scheduled']) is expected_result

    def _schedule_recordings(
            self,
            meeting,
            override_end_date=None,
            override_end_time=None,
            override_start_date=None,
            override_start_time=None,
    ):
        scheduled = Scheduled.create(
            instructor_uids=get_instructor_uids(term_id=self.term_id, section_id=self.section_id),
            kaltura_schedule_id=random.randint(1, 10),
            meeting_days='MO,WE,FR',
            meeting_end_date=override_end_date or get_recording_end_date(meeting),
            meeting_end_time=override_end_time or meeting['endTime'],
            meeting_start_date=override_start_date or get_recording_start_date(meeting, return_today_if_past_start=True),
            meeting_start_time=override_start_time or meeting['startTime'],
            publish_type_='kaltura_media_gallery',
            recording_type_='presenter_presentation_audio',
            room_id=Room.get_room_id(section_id=self.section_id, term_id=self.term_id),
            section_id=self.section_id,
            term_id=self.term_id,
        )
        if override_end_date or override_end_time or override_start_date or override_start_time:
            args = {
                'meeting_end_date': override_end_date,
                'meeting_end_time': override_end_time,
                'meeting_start_date': override_start_date,
                'meeting_start_time': override_start_time,
            }
            sql = 'UPDATE scheduled SET'
            previous_value = None
            for key, value in args.items():
                if value:
                    sql += f"{',' if previous_value else ''} {key} = :{key}"
                    previous_value = value
            sql += ' WHERE id = :id'
            db.session.execute(
                text(sql),
                {
                    **{'id': scheduled.id},
                    **args,
                },
            )
        std_commit(allow_test_environment=True)


class TestFirstDayRecording:

    def test_first_meeting_is_same_as_term_begin(self):
        """First meeting of course is the same day as first of term."""
        with override_config(app, 'CURRENT_TERM_BEGIN', _get_wednesday_august_26()):
            first_day_start = get_first_matching_datetime_of_term(
                meeting_days=['MO', 'WE', 'FR'],
                start_date=datetime.strptime(app.config['CURRENT_TERM_BEGIN'], '%Y-%m-%d'),
                time_hours=13,
                time_minutes=30,
            )
            assert first_day_start.day == 26

    def test_first_meeting_is_day_after_term_begin(self):
        """First meeting is the day after start of term."""
        with override_config(app, 'CURRENT_TERM_BEGIN', _get_wednesday_august_26()):
            first_day_start = get_first_matching_datetime_of_term(
                meeting_days=['TU', 'TH'],
                start_date=datetime.strptime(app.config['CURRENT_TERM_BEGIN'], '%Y-%m-%d'),
                time_hours=13,
                time_minutes=30,
            )
            assert first_day_start.day == 27

    def test_first_meeting_is_week_after_term_begin(self):
        """First meeting is the Monday following first week of term."""
        with override_config(app, 'CURRENT_TERM_BEGIN', _get_wednesday_august_26()):
            first_day_start = get_first_matching_datetime_of_term(
                meeting_days=['MO', 'TU'],
                start_date=datetime.strptime(app.config['CURRENT_TERM_BEGIN'], '%Y-%m-%d'),
                time_hours=8,
                time_minutes=45,
            )
            assert first_day_start.day == 31

    def test_first_meeting_is_different_month(self):
        """First meeting is in week after start of term, in a new month."""
        with override_config(app, 'CURRENT_TERM_BEGIN', _get_wednesday_august_26()):
            first_day_start = get_first_matching_datetime_of_term(
                meeting_days=['TU'],
                start_date=datetime.strptime(app.config['CURRENT_TERM_BEGIN'], '%Y-%m-%d'),
                time_hours=9,
                time_minutes=15,
            )
            assert first_day_start.month == 9
            assert first_day_start.day == 1

    def test_timestamps(self):
        """Epoch timestamp in PST timezone."""
        with override_config(app, 'CURRENT_TERM_BEGIN', _get_wednesday_august_26()):
            first_day_start = get_first_matching_datetime_of_term(
                meeting_days=['TU', 'TH'],
                start_date=datetime.strptime(app.config['CURRENT_TERM_BEGIN'], '%Y-%m-%d'),
                time_hours=9,
                time_minutes=37,
            )
            assert first_day_start.timestamp() == 1598546220.0


def _get_wednesday_august_26():
    # Aug 26, 2020, is a Wednesday.
    return '2020-08-26'


def _timezone():
    return pytz.timezone(app.config['TIMEZONE'])


def _format(date):
    return datetime.strftime(date, '%Y-%m-%d')


def _to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d')
