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
from contextlib import contextmanager
from datetime import datetime, timezone
from tempfile import TemporaryFile

from diablo.externals.kaltura import Kaltura
from diablo.models.room import Room
from flask import current_app as app

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


@contextmanager
def generate_ics_file(room_id, period_end_date, period_start_date):
    room = Room.get_room(room_id)
    if not room:
        app.logger.warning(f'Invalid room ID {room_id}; will not generate .ics file.')
        yield None
        return False
    if not len(room.scheduled):
        app.logger.warning(f'{room.location} has nothing scheduled between {period_start_date} and {period_end_date}; will not generate .ics file.')
        yield None
        return False

    app.logger.info(f'Generating .ics file for {room.location}, {period_start_date} to {period_end_date}')
    with TemporaryFile() as ics_file:
        ics_file.writelines(ICS_FILE_HEADER)
        for scheduled_course in room.scheduled:
            events = Kaltura().get_events_in_date_range(
                end_date=period_end_date,
                start_date=period_start_date,
                kaltura_schedule_id=scheduled_course.kaltura_schedule_id,
            )
            _write_course_meetings(scheduled_course, room.location, events, ics_file)
        ics_file.write(ICS_FILE_FOOTER)
        ics_file.seek(0)
        yield ics_file


def _write_course_meetings(scheduled_course, location, events, ics_file):
    section_id = scheduled_course.section_id
    if not len(events):
        app.logger.info(f'Found no events for section {section_id}.')
        return False
    app.logger.debug(f'Writing {len(events)} events for section {section_id} to .ics_file')
    for event in events:
        event_start_date = _to_utc(event.get('startDate'))
        event_end_date = _to_utc(event.get('endDate'))
        event_created_date = _to_utc(event.get('createdAt'))
        event_updated_date = _to_utc(event.get('updatedAt'))
        now = datetime.now(timezone.utc)
        unique_id = f"{_format_date(now)}@{app.config.get('EB_ENVIRONMENT', 'diablo-local')}"
        ics_file.writelines([
            b'BEGIN:VEVENT\n',
            b'CLASS:PUBLIC\n',
            bytes(f'CREATED:{_format_date(event_created_date)}\n', encoding='utf-8'),
            bytes(f"DESCRIPTION:{event.get('description')}\n", encoding='utf-8'),
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


def _format_date(d):
    return d.strftime('%Y%m%dT%H%M%SZ')


def _to_utc(date_str):
    return datetime.fromisoformat(date_str).astimezone(timezone.utc)
