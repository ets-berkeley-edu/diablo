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
from datetime import datetime
import io
import re
from zipfile import ZipFile

from diablo.lib.i_cal import generate_ics_file, get_zip_stream
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from flask import current_app as app
from tests.test_api.api_test_utils import mock_scheduled
from tests.util import test_scheduling_workflow


CREATED_DATE_PATTERN = re.compile(rb'CREATED:\d{8}T\d{6}Z\n')
START_DATE_PATTERN = re.compile(rb'DTSTART:\d{8}T\d{6}Z\n')
END_DATE_PATTERN = re.compile(rb'DTEND:\d{8}T\d{6}Z\n')
DATE_STAMP_PATTERN = re.compile(rb'DTSTAMP:\d{8}T\d{6}Z\n')
LAST_MODIFIED_PATTERN = re.compile(rb'LAST-MODIFIED:\d{8}T\d{6}Z\n')
UNIQUE_ID_PATTERN = re.compile(rb'UID:\d+\.\d+@diablo-test\n')

CURRENT_YEAR = datetime.now().year


def validate_header(ics_file):
    assert ics_file.readline() == b'BEGIN:VCALENDAR\n'
    assert ics_file.readline() == b'PRODID:-//Google Inc//Google Calendar 70.9054//EN\n'
    assert ics_file.readline() == b'VERSION:2.0\n'
    assert ics_file.readline() == b'CALSCALE:GREGORIAN\n'
    assert ics_file.readline() == b'METHOD:PUBLISH\n'
    assert ics_file.readline() == b'X-WR-CALNAME:iCal Test\n'
    assert ics_file.readline() == b'X-WR-TIMEZONE:America/Los_Angeles\n'


def validate_event(ics_file, section_id, location):
    assert ics_file.readline() == b'BEGIN:VEVENT\n'
    assert ics_file.readline() == b'CLASS:PUBLIC\n'
    assert CREATED_DATE_PATTERN.fullmatch(ics_file.readline())

    # description should wrap to 2 or 3 lines
    description = ics_file.readline()
    description += ics_file.readline()
    next_line = ics_file.readline()
    if not next_line.startswith(b'DTSTART:'):
        description += next_line
        next_line = ics_file.readline()
    # remove newlines and extra spaces added by text wrapping
    description = description.replace(b'\n', b'').replace(b'  ', b' ')
    assert description.startswith(b'DESCRIPTION:')
    assert description.decode().endswith(f'Copyright ©{CURRENT_YEAR} UC Regents; all rights reserved.')

    assert START_DATE_PATTERN.fullmatch(next_line)
    assert END_DATE_PATTERN.fullmatch(ics_file.readline())
    assert DATE_STAMP_PATTERN.fullmatch(ics_file.readline())
    assert LAST_MODIFIED_PATTERN.fullmatch(ics_file.readline())
    assert ics_file.readline() == bytes(f'LOCATION:{location}\n', encoding='utf-8')
    assert ics_file.readline() == b'SEQUENCE:0\n'
    assert ics_file.readline() == b'STATUS:CONFIRMED\n'
    assert ics_file.readline() == bytes(f'SUMMARY:qqq {section_id}\n', encoding='utf-8')
    assert ics_file.readline() == b'TRANSP:OPAQUE\n'
    assert UNIQUE_ID_PATTERN.fullmatch(ics_file.readline())
    assert ics_file.readline() == b'END:VEVENT\n'


def validate_footer(ics_file):
    assert ics_file.readline() == b'END:VCALENDAR'
    assert not ics_file.readline()


class TestGetIcsFiles:

    def test_no_scheduled_events(self):
        with test_scheduling_workflow(app):
            assert not get_zip_stream(datetime(2025, 6, 1), datetime(2025, 5, 30))

    def test_scheduled_events(self):
        filename_location_pattern = re.compile(r'([A-Za-z0-9_-]+)_\d{8}-\d{8}.ics')
        section_ids = [50000, 50001, 50002, 50003, 50004, 50005, 50006, 50007]
        with test_scheduling_workflow(app):
            for section_id in section_ids:
                mock_scheduled(section_id=section_id, term_id=2218)

            rooms = Room.all_rooms()
            room_schedules = {room.location.replace("'", ''): Scheduled.get_scheduled_per_room(room.id, term_id=2218) for room in rooms}
            zip_stream = get_zip_stream(datetime(2025, 6, 1), datetime(2025, 5, 30))
            assert zip_stream
            assert not zip_stream.testzip()

            body = b''
            for chunk in zip_stream:
                body += chunk
            zip_file = ZipFile(io.BytesIO(body), 'r')
            members = {}
            for name in zip_file.namelist():
                members[name] = zip_file.open(name)

            manifest_file = members.pop('_manifest.txt', None)
            assert manifest_file
            assert manifest_file.readline() == b'Total: 36 events in 3 rooms.\n'
            assert manifest_file.readline() == b'\n'
            assert manifest_file.readline() == b'Barker 101: 12 events\n'
            assert manifest_file.readline() == b'Li Ka Shing 145: 18 events\n'
            assert manifest_file.readline() == b"O'Brien 212: 6 events\n"
            assert not manifest_file.readline()

            for filename, ics_file in members.items():
                assert ics_file
                validate_header(ics_file)
                location_match = filename_location_pattern.findall(filename)[0]
                location = location_match.replace('_', ' ')
                for scheduled in room_schedules[location]:
                    for i in range(6):
                        validate_event(ics_file, scheduled.section_id, location)
                validate_footer(ics_file)
                ics_file.close()
                assert ics_file.closed
            zip_stream.close()


class TestGenerateIcsFile:

    def test_no_scheduled_events(self):
        room = Room.find_room("O'Brien 212")
        with test_scheduling_workflow(app):
            assert not generate_ics_file(room, datetime(2025, 6, 1), datetime(2025, 5, 30))

    def test_scheduled_events(self):
        term_id = 2218
        section_id = 50000
        room = Room.find_room("O'Brien 212")
        with test_scheduling_workflow(app):
            mock_scheduled(section_id, term_id, override_room_id=room.id)

            ics_file = generate_ics_file(room, datetime(2025, 6, 1), datetime(2025, 5, 30))
            assert ics_file
            validate_header(ics_file)
            location_alphanumeric = room.location.replace("'", '')
            for i in range(6):
                validate_event(ics_file, section_id, location_alphanumeric)
            validate_footer(ics_file)
            ics_file.close()
            assert ics_file.closed
