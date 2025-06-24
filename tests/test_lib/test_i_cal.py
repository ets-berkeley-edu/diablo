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
import re

from diablo.lib.i_cal import generate_ics_file
from diablo.models.room import Room
from tests.test_api.api_test_utils import mock_scheduled


class TestGenerateIcsFile:

    def test_nonexistent_room(self):
        with generate_ics_file(666, datetime(2025, 5, 30), datetime(2025, 6, 1)) as ics_file:
            assert not ics_file

    def test_no_scheduled_events(self):
        room = Room.find_room('Barker 101')
        with generate_ics_file(room.id, datetime(2025, 5, 30), datetime(2025, 6, 1)) as ics_file:
            assert not ics_file

    def test_scheduled_events(self):
        term_id = 2218
        section_id = 50000
        room = Room.find_room('Barker 101')
        mock_scheduled(section_id, term_id, override_room_id=room.id)

        with generate_ics_file(room.id, datetime(2025, 5, 30), datetime(2025, 6, 1)) as ics_file:
            assert ics_file
            assert ics_file.readline() == b'BEGIN:VCALENDAR\n'
            assert ics_file.readline() == b'PRODID:-//Google Inc//Google Calendar 70.9054//EN\n'
            assert ics_file.readline() == b'VERSION:2.0\n'
            assert ics_file.readline() == b'CALSCALE:GREGORIAN\n'
            assert ics_file.readline() == b'METHOD:PUBLISH\n'
            assert ics_file.readline() == b'X-WR-CALNAME:iCal Test\n'
            assert ics_file.readline() == b'X-WR-TIMEZONE:America/Los_Angeles\n'
            for i in range(6):
                assert ics_file.readline() == b'BEGIN:VEVENT\n'
                assert ics_file.readline() == b'CLASS:PUBLIC\n'
                assert re.fullmatch(rb'CREATED:\d{8}T\d{6}Z\n', ics_file.readline())
                assert ics_file.readline().startswith(b'DESCRIPTION:')
                assert re.fullmatch(rb'DTSTART:\d{8}T\d{6}Z\n', ics_file.readline())
                assert re.fullmatch(rb'DTEND:\d{8}T\d{6}Z\n', ics_file.readline())
                assert re.fullmatch(rb'DTSTAMP:\d{8}T\d{6}Z\n', ics_file.readline())
                assert re.fullmatch(rb'LAST-MODIFIED:\d{8}T\d{6}Z\n', ics_file.readline())
                assert ics_file.readline() == b'LOCATION:Barker 101\n'
                assert ics_file.readline() == b'SEQUENCE:0\n'
                assert ics_file.readline() == b'STATUS:CONFIRMED\n'
                assert ics_file.readline() == bytes(f'SUMMARY:qqq {section_id}\n', encoding='utf-8')
                assert ics_file.readline() == b'TRANSP:OPAQUE\n'
                assert re.fullmatch(rb'UID:\d{8}T\d{6}Z@diablo-test\n', ics_file.readline())
                assert ics_file.readline() == b'END:VEVENT\n'
