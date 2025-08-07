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
from datetime import datetime, timezone
from tempfile import TemporaryFile
from textwrap import TextWrapper

import zipstream
from flask import current_app as app
from KalturaClient.Plugins.Schedule import KalturaScheduleEventRecurrenceType, KalturaScheduleEventStatus

from diablo.externals.kaltura import Kaltura
from diablo.lib.util import utc_now
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled

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
KALTURA_TEXT_ENCODING = 'latin-1'
NON_ALPHANUMERIC_PATTERN = re.compile(r'[^a-zA-Z0-9 -]')

wrapper = TextWrapper(expand_tabs=False, drop_whitespace=False, subsequent_indent=' ')


def get_zip_stream(period_end_date, period_start_date):
    rooms = Room.get_eligible_rooms()
    if not len(rooms):
        app.logger.warning('No eligible rooms found; will not generate .ics files')

    app.logger.info(f'Exporting events to iCalendar for {len(rooms)} eligible rooms')
    kaltura = Kaltura()
    zip_stream = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
    manifest = []
    total_events = 0
    for room in rooms:
        events, count = _get_scheduled_events(kaltura, room, period_end_date, period_start_date)
        if count:
            zip_stream.write_iter(
                get_ics_file_name(room.location, period_start_date, period_end_date),
                _ics_generator(events),
            )
            manifest.append(f'{room.location}: {count} events\n')
            total_events += count
    if len(zip_stream.paths_to_write):
        zip_stream.write_iter('_manifest.txt', _manifest_generator(manifest, total_events))
        return zip_stream
    else:
        return None


def generate_ics_file(room, period_end_date, period_start_date):
    kaltura = Kaltura()
    events, count = _get_scheduled_events(kaltura, room, period_end_date, period_start_date)
    if count:
        ics_file = TemporaryFile()
        ics_file.writelines(_ics_generator(events))
        ics_file.seek(0)
        return ics_file


def get_ics_file_name(location, start_date, end_date):
    location_alphanumeric = get_kaltura_safe_name(location)
    return f"{location_alphanumeric.replace(' ', '_')}_{_format_date_for_filename(start_date)}-{_format_date_for_filename(end_date)}.ics"


def get_kaltura_safe_name(location):
    return NON_ALPHANUMERIC_PATTERN.sub('', location.replace('&', 'and'))


def get_zip_file_name(start_date, end_date):
    return f'iCal_export_{_format_date_for_filename(start_date)}-{_format_date_for_filename(end_date)}.zip'


def _get_scheduled_events(kaltura, room, period_end_date, period_start_date, count=None):
    schedule = Scheduled.get_scheduled_per_room(
        room_id=room.id,
        term_id=app.config['CURRENT_TERM_ID'],
    )
    if not len(schedule):
        app.logger.info(f'{room.location} has nothing scheduled for the current term; will not generate .ics file')

    location_alphanumeric = get_kaltura_safe_name(room.location)
    formatted_events = []
    count = 0
    for scheduled_course in schedule:
        course_meetings = kaltura.get_events_in_date_range(
            end_date=period_end_date,
            start_date=period_start_date,
            kaltura_schedule_id=scheduled_course.kaltura_schedule_id,
            recurrence_type=KalturaScheduleEventRecurrenceType.RECURRENCE,
            status=KalturaScheduleEventStatus.ACTIVE,
        )
        formatted_events.extend(_events_to_ics_format(location_alphanumeric, scheduled_course.section_id, course_meetings))
        count += len(course_meetings)
    if count:
        app.logger.info(
            f'Generating .ics file for {room.location} with {count} events between {period_start_date} and {period_end_date}',
        )
    else:
        app.logger.info(
            f'No Kaltura events found for {room.location} between {period_start_date} and {period_end_date}; will not generate .ics file',
        )
    return formatted_events, count


def _events_to_ics_format(location, section_id, events):
    host = app.config.get('EB_ENVIRONMENT', 'diablo-local')
    now = utc_now()
    ics_events = []
    for index, event in enumerate(events):
        event_start_date = _to_utc(event.get('startDate'))
        event_end_date = _to_utc(event.get('endDate'))
        event_created_date = _to_utc(event.get('createdAt'))
        event_updated_date = _to_utc(event.get('updatedAt'))
        description = f"DESCRIPTION:{event.get('description')}"
        unique_id = f'{now.timestamp()}{index}@{host}'
        ics_events.extend([
            'BEGIN:VEVENT\n',
            'CLASS:PUBLIC\n',
            f'CREATED:{_format_date_for_ical(event_created_date)}\n',
            f'{_wrap_text(description, wrapper)}\n',
            f'DTSTART:{_format_date_for_ical(event_start_date)}\n',
            f'DTEND:{_format_date_for_ical(event_end_date)}\n',
            f'DTSTAMP:{_format_date_for_ical(now)}\n',
            f'LAST-MODIFIED:{_format_date_for_ical(event_updated_date)}\n',
            f'LOCATION:{location}\n',
            'SEQUENCE:0\n',
            'STATUS:CONFIRMED\n',
            f'SUMMARY:{ICS_SUMMARY_PREFIX} {section_id}\n',
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
        yield bytes(line, encoding=KALTURA_TEXT_ENCODING)
    for line in events:
        yield bytes(line, encoding=KALTURA_TEXT_ENCODING)
    yield bytes(ICS_FILE_FOOTER, encoding=KALTURA_TEXT_ENCODING)


def _manifest_generator(manifest, total_events):
    yield bytes(f'Total: {total_events} events in {len(manifest)} rooms.\n\n', encoding=KALTURA_TEXT_ENCODING)
    for line in manifest:
        yield bytes(line, encoding=KALTURA_TEXT_ENCODING)


def _to_utc(date_str):
    return datetime.fromisoformat(date_str).astimezone(timezone.utc)


def _wrap_text(line, wrapper):
    return '\n'.join(wrapper.wrap(line))
