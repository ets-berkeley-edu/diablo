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

from diablo import cache
from diablo.externals.salesforce import get_all_salesforce_rooms
from diablo.lib.salesforce_utils import convert_military_time, days_of_week_for_salesforce, \
    get_salesforce_location_id, is_course_in_capture_enabled_room
from pytest import raises


class TestTimeTranslation:

    def test_convert_blank(self):
        for blank in (None, '', '  '):
            assert convert_military_time(blank) is None

    def test_value_error(self):
        for invalid_time in ('blargh', '30:00', '24:30', '4:65'):
            with raises(ValueError):
                convert_military_time(invalid_time)

    def test_midnight(self):
        assert convert_military_time('24:00') == '12:00am'

    def test_morning(self):
        assert convert_military_time('00:59') == '00:59am'

    def test_noon(self):
        assert convert_military_time('12:00') == '12:00pm'

    def test_afternoon(self):
        assert convert_military_time('13:59') == '01:59pm'


class TestWeekdaysTranslation:

    def test_convert_blank(self):
        for blank in (None, '', '  '):
            assert days_of_week_for_salesforce(blank) is None

    def test_value_error(self):
        for invalid_days in ('blargh', 'Mon', 'TUTHZO'):
            with raises(ValueError):
                days_of_week_for_salesforce(invalid_days)

    def test_valid_days(self):
        assert days_of_week_for_salesforce('tuth') == 'Tuesday, Thursday'
        assert days_of_week_for_salesforce('FR') == 'Friday'
        assert days_of_week_for_salesforce('FRMOWE') == 'Monday, Wednesday, Friday'


class TestRoomComparison:

    def test_room_normalization(self):
        all_locations = get_all_salesforce_rooms()
        assert get_salesforce_location_id({'location': '  BARROWS 106 '}, all_locations) == 'a0619000005LtFgAAK'
        assert get_salesforce_location_id({'location': '  BARROWS 107 '}, all_locations) is None

    def test_genetics_plant_bio_location(self):
        location_id = get_salesforce_location_id({'location': 'Genetics & Plant Bio 105'}, get_all_salesforce_rooms())
        assert location_id == 'a0619000005LtGPAA0'

    def test_course_in_capture_enabled_room(self):
        all_rooms = cache.get('salesforce/all_rooms')
        assert is_course_in_capture_enabled_room(
            {
                'location': ' HERTZ  320 ',
            },
            all_rooms,
        )

    def test_course_not_in_capture_enabled_room(self):
        all_rooms = cache.get('salesforce/all_rooms')
        assert not is_course_in_capture_enabled_room(
            {
                'location': 'Hertz 222',
            },
            all_rooms,
        )
        assert not is_course_in_capture_enabled_room(
            {
                'location': 'Stanley 105',
            },
            all_rooms,
        )
