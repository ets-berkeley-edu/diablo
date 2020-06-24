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
from datetime import datetime

from diablo.lib.kaltura_util import get_first_matching_datetime_of_term
from flask import current_app as app
import pytz
from tests.util import override_config


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
