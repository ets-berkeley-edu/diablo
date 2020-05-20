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

from diablo.api.errors import BadRequestError, ResourceNotFoundError
from diablo.api.util import admin_required
from diablo.externals.kaltura import Kaltura
from diablo.lib.http import tolerant_jsonify
from diablo.models.room import Room
from diablo.models.sis_section import SisSection
from flask import current_app as app, request


@app.route('/api/rooms/all')
@admin_required
def get_all_rooms():
    return tolerant_jsonify([room.to_api_json() for room in Room.all_rooms()])


@app.route('/api/rooms/kaltura_resources')
@admin_required
def kaltura_resource_list():
    return tolerant_jsonify(Kaltura().get_resource_list())


@app.route('/api/room/<room_id>/kaltura_event_list')
@admin_required
def kaltura_event_list(room_id):
    room = Room.get_room(room_id)
    if room and room.kaltura_resource_id:
        return tolerant_jsonify(Kaltura().get_events_by_location(kaltura_resource_id=room.kaltura_resource_id))
    else:
        raise ResourceNotFoundError('No such room')


@app.route('/api/room/<room_id>')
@admin_required
def get_room(room_id):
    room = Room.get_room(room_id)
    if room:
        api_json = room.to_api_json()
        api_json['courses'] = SisSection.get_courses_per_location(
            term_id=app.config['CURRENT_TERM_ID'],
            location=room.location,
        )
        return tolerant_jsonify(api_json)
    else:
        raise ResourceNotFoundError('No such room')


@app.route('/api/room/auditorium', methods=['POST'])
@admin_required
def auditorium():
    params = request.get_json()
    room_id = params.get('roomId')
    room = Room.get_room(room_id) if room_id else None
    if room:
        is_auditorium = params.get('isAuditorium')
        if not room_id or is_auditorium is None:
            raise BadRequestError('\'roomId\' and \'isAuditorium\' are required.')
        room = Room.set_auditorium(room_id, is_auditorium)
        return tolerant_jsonify(room.to_api_json())
    else:
        raise ResourceNotFoundError('No such room')


@app.route('/api/room/update_capability', methods=['POST'])
@admin_required
def update_room_capability():
    params = request.get_json()
    room_id = params.get('roomId')
    room = Room.get_room(room_id) if room_id else None
    if not room or 'capability' not in params:
        raise BadRequestError('Missing required parameters')
    capability = params.get('capability')
    room = Room.update_capability(room_id, capability)
    return tolerant_jsonify(room.to_api_json())
