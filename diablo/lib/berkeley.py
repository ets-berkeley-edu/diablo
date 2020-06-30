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

from flask import current_app as app


def flatten_location(name):
    return name and ''.join(name.split()).lower()


def get_recording_end_date(meeting):
    term_end = datetime.strptime(app.config['CURRENT_TERM_RECORDINGS_END'], '%Y-%m-%d')
    actual_end = datetime.strptime(meeting['endDate'].split()[0], '%Y-%m-%d')
    return actual_end if actual_end < term_end else term_end


def get_recording_start_date(meeting, return_today_if_past_start=False):
    term_begin = datetime.strptime(app.config['CURRENT_TERM_RECORDINGS_BEGIN'], '%Y-%m-%d')
    actual_start = datetime.strptime(meeting['startDate'].split()[0], '%Y-%m-%d')
    start_date = actual_start if actual_start > term_begin else term_begin
    today = datetime.today()
    return today if start_date < today and return_today_if_past_start else start_date


def scheduled_dates_are_obsolete(meeting, scheduled):
    if meeting:
        def _format(date):
            return datetime.strftime(date, '%Y-%m-%d')
        expected_start_date = get_recording_start_date(meeting, return_today_if_past_start=False)
        expected_end_date = get_recording_end_date(meeting)
        # Is the schedule-of-recordings in Kaltura still valid?
        start_date_mismatch = _format(expected_start_date) != scheduled['meetingStartDate']
        end_date_mismatch = _format(expected_end_date) != scheduled['meetingEndDate']
        # If recordings were scheduled AFTER the meeting_start_date then we will ignore start_date_mismatch
        scheduled_after_start_date = scheduled['createdAt'][0:10] > _format(expected_start_date)
        return end_date_mismatch if scheduled_after_start_date else (start_date_mismatch or end_date_mismatch)
    else:
        return True


def term_name_for_sis_id(sis_id=None):
    if sis_id:
        sis_id = str(sis_id)
        season_codes = {
            '0': 'Winter',
            '2': 'Spring',
            '5': 'Summer',
            '8': 'Fall',
        }
        year = f'19{sis_id[1:3]}' if sis_id.startswith('1') else f'20{sis_id[1:3]}'
        return f'{season_codes[sis_id[3:4]]} {year}'
