"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from textwrap import TextWrapper

import zipstream
from dateutil.rrule import WEEKLY, rrule
from flask import current_app as app

from diablo.lib.berkeley import DAYS, get_first_matching_datetime_of_term, term_name_for_sis_id
from diablo.lib.kaltura_util import get_series_description
from diablo.lib.util import default_timezone, format_days, utc_now
from diablo.models.blackout import Blackout
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection

"""Converts Kaltura schedule events to an iCalendar file in conformance with RFC 5545."""


ICS_FILE_HEADER = [
    'BEGIN:VCALENDAR\n',
    'PRODID:-//Google Inc//Google Calendar 70.9054//EN\n',
    'VERSION:2.0\n',
    'CALSCALE:GREGORIAN\n',
    'METHOD:PUBLISH\n',
    'X-WR-CALNAME:iCal Test\n',
    'X-WR-TIMEZONE:America/Los_Angeles\n',
]
ICS_FILE_FOOTER = 'END:VCALENDAR'
# The prefix makes these events easily searchable in Kaltura
ICS_SUMMARY_PREFIX = 'qqq'
NON_ALPHANUMERIC_PATTERN = re.compile(r'[^a-zA-Z0-9 -]')

wrapper = TextWrapper(expand_tabs=False, drop_whitespace=False, subsequent_indent=' ')


def get_zip_stream(period_end_date, period_start_date):
    rooms = Room.get_eligible_rooms()
    if not len(rooms):
        app.logger.warning('No eligible rooms found; will not generate .ics files')

    app.logger.info(f'Exporting events to iCalendar for {len(rooms)} eligible rooms')
    zip_stream = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
    manifest = []
    total_events = 0
    for room in rooms:
        events = _get_scheduled_events(room, period_end_date, period_start_date)
        if len(events):
            zip_stream.write_iter(
                get_ics_file_name(room.location, period_start_date, period_end_date),
                _ics_generator(events),
            )
            manifest.append(f'{room.location}: {len(events)} events\n')
            total_events += len(events)
    if len(zip_stream.paths_to_write):
        zip_stream.write_iter('_manifest.txt', _manifest_generator(manifest, total_events))
        return zip_stream
    else:
        return None


def get_ics_file_name(location, start_date, end_date):
    location_alphanumeric = get_kaltura_safe_name(location)
    return f"{location_alphanumeric.replace(' ', '_')}_{_format_date_for_filename(start_date)}-{_format_date_for_filename(end_date)}.ics"


def get_kaltura_safe_name(location):
    normalized = unicodedata.normalize('NFKC', location).replace('&', 'and')
    return NON_ALPHANUMERIC_PATTERN.sub('', normalized)


def get_zip_file_name(start_date, end_date):
    return f'iCal_export_{_format_date_for_filename(start_date)}-{_format_date_for_filename(end_date)}.zip'


def _get_scheduled_events(room, period_end_date, period_start_date, count=None):
    schedule = Scheduled.get_scheduled_per_room(
        room_id=room.id,
        term_id=app.config['CURRENT_TERM_ID'],
    )
    if not len(schedule):
        app.logger.info(f'{room.location} has nothing scheduled for the current term; will not generate .ics file')

    location_alphanumeric = get_kaltura_safe_name(room.location)
    formatted_events = []
    for scheduled_course in schedule:
        dates = _generate_recurrent_dates(scheduled_course, period_start_date, period_end_date)
        course_feed = SisSection.get_course(
            include_update_history=False,
            term_id=scheduled_course.term_id,
            section_id=scheduled_course.section_id,
        )
        if course_feed:
            series_description = get_series_description(
                course_label=course_feed['label'],
                instructors=course_feed['instructors'],
                term_name=term_name_for_sis_id(course_feed['termId']),
            )
            ics_events = _events_to_ics_format(
                dates=dates,
                location=location_alphanumeric,
                scheduled_course=scheduled_course,
                series_description=series_description,
            )
            formatted_events.extend(ics_events)
    if len(formatted_events):
        app.logger.info(
            f'Generating .ics file for {room.location} with {len(formatted_events)} events between {period_start_date} and {period_end_date}',
        )
    else:
        app.logger.info(
            f'No Kaltura events found for {room.location} between {period_start_date} and {period_end_date}; will not generate .ics file',
        )
    return formatted_events


def _generate_recurrent_dates(scheduled_course, period_start_date, period_end_date):
    tz = default_timezone()

    def _localize_timezone(dt):
        return tz.localize(datetime(dt.year, dt.month, dt.day))

    start_bound = _localize_timezone(period_start_date)
    end_bound = _localize_timezone(period_end_date)

    start_date = max(_localize_timezone(scheduled_course.meeting_start_date), start_bound)
    end_date = min(_localize_timezone(scheduled_course.meeting_end_date), end_bound)
    days = format_days(scheduled_course.meeting_days)

    dtstart = get_first_matching_datetime_of_term(
        meeting_days=days,
        start_date=start_date,
        time_hours=0,
        time_minutes=0,
    )
    until_local_tz = tz.localize(datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999))

    return rrule(freq=WEEKLY, dtstart=dtstart, until=until_local_tz, byweekday=[DAYS.index(d) for d in days])


def _events_to_ics_format(location, scheduled_course, series_description, dates):
    host = app.config.get('EB_ENVIRONMENT', 'diablo-local')
    now = utc_now()
    ics_events = []
    blackouts = Blackout.all_blackouts()

    def _adjust_timestamp(date, military_time, offset_minutes):
        tz = default_timezone()
        hour_and_minutes = military_time.split(':')
        hour = int(hour_and_minutes[0])
        minutes = int(hour_and_minutes[1])
        local_dt = tz.localize(datetime(
            date.year,
            date.month,
            date.day,
            hour,
            minutes,
        )) + timedelta(minutes=offset_minutes)
        return local_dt.astimezone(timezone.utc)

    for index, date in enumerate(dates):
        event_start_date = _adjust_timestamp(date, scheduled_course.meeting_start_time, app.config['KALTURA_RECORDING_OFFSET_START'])
        event_end_date = _adjust_timestamp(date, scheduled_course.meeting_end_time, app.config['KALTURA_RECORDING_OFFSET_END'])

        blacked_out = False
        for blackout in blackouts:
            if event_start_date < blackout.end_date and event_end_date > blackout.start_date:
                blacked_out = True
        if blacked_out:
            continue

        event_created_date = scheduled_course.created_at.astimezone(timezone.utc)
        description = f"DESCRIPTION:{series_description}"
        unique_id = f'{now.timestamp()}{index}@{host}'
        ics_events.extend([
            'BEGIN:VEVENT\n',
            'CLASS:PUBLIC\n',
            f'CREATED:{_format_date_for_ical(event_created_date)}\n',
            f'{_wrap_text(description, wrapper)}\n',
            f'DTSTART:{_format_date_for_ical(event_start_date)}\n',
            f'DTEND:{_format_date_for_ical(event_end_date)}\n',
            f'DTSTAMP:{_format_date_for_ical(now)}\n',
            f'LAST-MODIFIED:{_format_date_for_ical(event_created_date)}\n',
            f'LOCATION:{location}\n',
            'SEQUENCE:0\n',
            'STATUS:CONFIRMED\n',
            f'SUMMARY:{ICS_SUMMARY_PREFIX} {scheduled_course.section_id}\n',
            'TRANSP:OPAQUE\n',
            f'UID:{unique_id}\n',
            'END:VEVENT\n',
        ])
    return ics_events


def _format_date_for_ical(d):
    return d.strftime('%Y%m%dT%H%M%SZ')


def _format_date_for_filename(d):
    return d.strftime('%Y%m%d')


def _ics_generator(events):
    for line in ICS_FILE_HEADER:
        yield bytes(line, encoding='utf-8')
    for line in events:
        yield bytes(line, encoding='utf-8')
    yield bytes(ICS_FILE_FOOTER, encoding='utf-8')


def _manifest_generator(manifest, total_events):
    yield bytes(f'Total: {total_events} events in {len(manifest)} rooms.\n\n', encoding='utf-8')
    for line in manifest:
        yield bytes(line, encoding='utf-8')


def _to_utc(date_str):
    return datetime.fromisoformat(date_str).astimezone(timezone.utc)


def _wrap_text(line, wrapper):
    return '\n'.join(wrapper.wrap(line))
