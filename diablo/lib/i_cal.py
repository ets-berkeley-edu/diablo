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
from datetime import datetime, timezone
from tempfile import TemporaryFile
from textwrap import TextWrapper

from diablo.externals.kaltura import Kaltura
from flask import current_app as app
from KalturaClient.Plugins.Schedule import KalturaScheduleEventRecurrenceType


"""Converts Kaltura schedule events to an iCalendar file in conformance with RFC 5545."""


ICS_FILE_HEADER = [
    b'BEGIN:VCALENDAR\n',
    b'PRODID:-//Google Inc//Google Calendar 70.9054//EN\n',
    b'VERSION:2.0\n',
    b'CALSCALE:GREGORIAN\n',
    b'METHOD:PUBLISH\n',
    b'X-WR-CALNAME:iCal Test\n',
    b'X-WR-TIMEZONE:America/Los_Angeles\n',
]
ICS_FILE_FOOTER = b'END:VCALENDAR'
# The prefix makes these events easily searchable in Kaltura
ICS_SUMMARY_PREFIX = 'qqq'


def generate_ics_file(room, period_end_date, period_start_date):
    if not len(room.scheduled):
        app.logger.info(f'{room.location} has nothing scheduled between {period_start_date} and {period_end_date}; will not generate .ics file.')
        return None

    app.logger.info(f'Generating .ics file for {room.location}, {period_start_date} to {period_end_date}')
    wrapper = TextWrapper(expand_tabs=False, drop_whitespace=False, subsequent_indent=' ')
    events = []
    for scheduled_course in room.scheduled:
        course_events = Kaltura().get_events_in_date_range(
            end_date=period_end_date,
            start_date=period_start_date,
            kaltura_schedule_id=scheduled_course.kaltura_schedule_id,
            recurrence_type=KalturaScheduleEventRecurrenceType.RECURRENCE,
        )
        if len(course_events):
            events.extend(_format_events(room.location, scheduled_course.section_id, course_events, wrapper))
    if not len(events):
        app.logger.info(
            f'No Kaltura events found for {room.location} between {period_start_date} and {period_end_date}; will not generate .ics file.',
        )
        return None

    ics_file = TemporaryFile()
    ics_file.writelines(ICS_FILE_HEADER)
    app.logger.debug(f'Writing {len(events)} events for {room.location} to .ics file')
    ics_file.writelines(events)
    ics_file.write(ICS_FILE_FOOTER)
    ics_file.seek(0)
    return ics_file


def _format_events(location, section_id, events, wrapper):
    host = app.config.get('EB_ENVIRONMENT', 'diablo-local')
    now = datetime.now(timezone.utc)
    ics_events = []
    for index, event in enumerate(events):
        event_start_date = _to_utc(event.get('startDate'))
        event_end_date = _to_utc(event.get('endDate'))
        event_created_date = _to_utc(event.get('createdAt'))
        event_updated_date = _to_utc(event.get('updatedAt'))
        description = f"DESCRIPTION:{event.get('description')}"
        unique_id = f'{now.timestamp()}{index}@{host}'
        ics_events.extend([
            b'BEGIN:VEVENT\n',
            b'CLASS:PUBLIC\n',
            bytes(f'CREATED:{_format_date(event_created_date)}\n', encoding='utf-8'),
            bytes(f'{_wrap_text(description, wrapper)}\n', encoding='utf-8'),
            bytes(f'DTSTART:{_format_date(event_start_date)}\n', encoding='utf-8'),
            bytes(f'DTEND:{_format_date(event_end_date)}\n', encoding='utf-8'),
            bytes(f'DTSTAMP:{_format_date(now)}\n', encoding='utf-8'),
            bytes(f'LAST-MODIFIED:{_format_date(event_updated_date)}\n', encoding='utf-8'),
            bytes(f'LOCATION:{location}\n', encoding='utf-8'),
            b'SEQUENCE:0\n',
            b'STATUS:CONFIRMED\n',
            bytes(f'SUMMARY:{ICS_SUMMARY_PREFIX} {section_id}\n', encoding='utf-8'),
            b'TRANSP:OPAQUE\n',
            bytes(f'UID:{unique_id}\n', encoding='utf-8'),
            b'END:VEVENT\n',
        ])
    return ics_events


def _format_date(d):
    return d.strftime('%Y%m%dT%H%M%SZ')


def _wrap_text(line, wrapper):
    return '\n'.join(wrapper.wrap(line))


def _to_utc(date_str):
    return datetime.fromisoformat(date_str).astimezone(timezone.utc)
