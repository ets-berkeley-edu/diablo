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
from datetime import datetime, timedelta

from diablo.lib.util import default_timezone, format_days, safe_strftime
from flask import current_app as app

# This order of days is aligned with datetime module: https://pythontic.com/datetime/date/weekday
DAYS = ('MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU')


def flatten_location(name):
    return name and ''.join(name.split()).lower()


def get_first_matching_datetime_of_term(meeting_days, start_date, time_hours, time_minutes):
    first_meeting = None
    meeting_day_indices = [DAYS.index(day) for day in meeting_days]
    for index in range(7):
        # Monday is 0 and Sunday is 6
        day_index = (start_date.weekday() + index) % 7
        if day_index in meeting_day_indices:
            first_day = start_date + timedelta(days=index)
            first_meeting = default_timezone().localize(
                datetime(
                    first_day.year,
                    first_day.month,
                    first_day.day,
                    time_hours,
                    time_minutes,
                ),
            )
            break
    return first_meeting


def get_recording_end_date(meeting):
    term_end = datetime.strptime(app.config['CURRENT_TERM_RECORDINGS_END'], '%Y-%m-%d')
    actual_end_date = meeting['endDate']
    actual_end = datetime.strptime(actual_end_date.split()[0], '%Y-%m-%d') if actual_end_date else None
    end_date = (actual_end if actual_end < term_end else term_end) if actual_end else None
    # Determine first course meeting BEFORE end_date.
    last_recording = None
    meeting_day_indices = [DAYS.index(day) for day in format_days(meeting['days'])]
    for index in range(7):
        # Monday is 0 and Sunday is 6
        day_index = ((end_date.weekday() - index) % 7) if end_date else None
        if day_index in meeting_day_indices:
            last_day = end_date - timedelta(days=index)
            last_recording = datetime(last_day.year, last_day.month, last_day.day)
            break
    return last_recording


def get_recording_start_date(meeting, return_today_if_past_start=False):
    term_begin = datetime.strptime(app.config['CURRENT_TERM_RECORDINGS_BEGIN'], '%Y-%m-%d')
    actual_start_date = meeting['startDate']
    actual_start = datetime.strptime(actual_start_date.split()[0], '%Y-%m-%d') if actual_start_date else None
    start_date = (actual_start if actual_start > term_begin else term_begin) if actual_start else None
    today = datetime.today()
    start_date = today if (start_date and start_date < today and return_today_if_past_start) else start_date
    # Determine first course meeting AFTER start_date.
    first_recording = None
    meeting_day_indices = [DAYS.index(day) for day in format_days(meeting['days'])]
    for index in range(7):
        # Monday is 0 and Sunday is 6
        day_index = (start_date.weekday() + index) % 7 if start_date else None
        if day_index in meeting_day_indices:
            first_day = start_date + timedelta(days=index)
            first_recording = datetime(first_day.year, first_day.month, first_day.day)
            break
    return first_recording


def term_name_for_sis_id(sis_id=None):
    if sis_id:
        sis_id = str(sis_id)
        season_codes = {
            '0': 'Winter',
            '2': 'Spring',
            '5': 'Summer',
            '8': 'Fall',
        }
        return f'{season_codes[sis_id[3:4]]} {term_year_for_sis_id(sis_id)}'


def term_year_for_sis_id(sis_id=None):
    if sis_id:
        sis_id = str(sis_id)
        return f'19{sis_id[1:3]}' if sis_id.startswith('1') else f'20{sis_id[1:3]}'


def get_canvas_sis_term_id(sis_id=None):
    if sis_id:
        sis_id = str(sis_id)
        season_codes = {
            '0': 'A',
            '2': 'B',
            '5': 'C',
            '8': 'D',
        }
        year = f'19{sis_id[1:3]}' if sis_id.startswith('1') else f'20{sis_id[1:3]}'
        return f'TERM:{year}-{season_codes[sis_id[3:4]]}'


def are_scheduled_dates_obsolete(meeting, scheduled):
    if meeting:
        recording_start_date = get_recording_start_date(meeting, return_today_if_past_start=False)
        formatted_start_date = safe_strftime(recording_start_date, '%Y-%m-%d')
        start_date_mismatch = formatted_start_date != scheduled['meetingStartDate']

        recording_end_date = get_recording_end_date(meeting)
        end_date_mismatch = safe_strftime(recording_end_date, '%Y-%m-%d') != scheduled['meetingEndDate']

        # If recordings were scheduled AFTER the meeting_start_date then we will ignore start_date_mismatch
        scheduled_after_start_date = formatted_start_date and scheduled['createdAt'][0:10] > formatted_start_date
        return end_date_mismatch if scheduled_after_start_date else (start_date_mismatch or end_date_mismatch)
    else:
        return True


def are_scheduled_times_obsolete(meeting, scheduled):
    if meeting:
        return serialize_sis_meeting_time(meeting) != serialize_scheduled_meeting_time(scheduled)
    else:
        return True


def serialize_scheduled_meeting_time(scheduled):
    return '-'.join(
        [
            str(scheduled['meetingDays']),
            scheduled['meetingStartTime'],
            scheduled['meetingEndTime'],
        ],
    )


def serialize_sis_meeting_time(meeting):
    return '-'.join(
        [
            str(meeting['daysFormatted']),
            str(meeting['startTime']),
            str(meeting['endTime']),
        ],
    )
