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

from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from flask import current_app as app
from tests.util import override_config


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
            assert datetime.strftime(get_recording_start_date(meeting), df) == datetime.strftime(today, df)


def _to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d')
