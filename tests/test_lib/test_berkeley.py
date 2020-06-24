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

from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from flask import current_app as app
from tests.util import override_config


class TestRecordingDates:

    def test_recording_end_date(self):
        diablo_end = '2020-11-25'
        with override_config(app, 'CURRENT_TERM_END', diablo_end):
            def _get_recording_end_date(end_date):
                return get_recording_end_date(meeting={'endDate': end_date})
            assert _get_recording_end_date('2020-12-11 00:00:00 UTC') == _to_datetime(diablo_end)
            assert _get_recording_end_date('2020-11-01 00:00:00 UTC') == _to_datetime('2020-11-01')

    def test_recording_start_date(self):
        diablo_start = '2020-09-07'
        with override_config(app, 'CURRENT_TERM_BEGIN', diablo_start):
            def _get_recording_start_date(start_date):
                return get_recording_start_date(meeting={'startDate': start_date})
            assert _get_recording_start_date('2020-08-26 00:00:00 UTC') == _to_datetime(diablo_start)
            assert _get_recording_start_date('2020-09-14 00:00:00 UTC') == _to_datetime('2020-09-14')


def _to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d')
