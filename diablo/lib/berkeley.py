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

from diablo.models.approval import RECORDING_TYPE_NAMES_PER_ID


def get_capture_options(location, enabled_rooms):
    def _flatten_location(name):
        return name and ''.join(name.split()).lower()

    room_capabilities = []
    flattened_location = _flatten_location(location)
    for enabled_room in enabled_rooms:
        _flattened_enabled_location = _flatten_location(f'{enabled_room["building"]} {enabled_room["roomNumber"]}')
        if flattened_location == _flattened_enabled_location:
            if enabled_room['capabilities'] == 'Screencast + Video':
                for key, value in RECORDING_TYPE_NAMES_PER_ID.items():
                    room_capabilities.append({
                        'text': value,
                        'value': key,
                    })
            else:
                key = 'presentation_audio'
                room_capabilities.append({
                    'text': RECORDING_TYPE_NAMES_PER_ID[key],
                    'value': key,
                })
            break
    return room_capabilities


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
