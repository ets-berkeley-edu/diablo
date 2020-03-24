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
from diablo.lib.http import tolerant_jsonify
from diablo.models.approval import Approval
from diablo.models.room import Room
from flask import current_app as app, request


@app.route('/api/berkeley/all_rooms')
@admin_required
def get_all_rooms():
    return tolerant_jsonify([room.to_api_json() for room in Room.all_rooms()])


@app.route('/api/berkeley/capability_options')
@admin_required
def get_capability_options():
    api_json = []
    for value, label in Room.get_room_capability_options().items():
        api_json.append({
            'label': label,
            'value': value,
        })
    return tolerant_jsonify(api_json)


@app.route('/api/berkeley/room/<room_id>')
@admin_required
def get_room(room_id):
    room = Room.get_room(room_id)
    if room:
        term_id = app.config['CURRENT_TERM_ID']
        api_json = room.to_api_json()
        api_json['approvals'] = [approval.to_api_json() for approval in Approval.get_approvals_per_room_id(room_id=room.id, term_id=term_id)]
        return tolerant_jsonify(api_json)
    else:
        raise ResourceNotFoundError('No such room')


@app.route('/api/berkeley/update_room_capability', methods=['POST'])
@admin_required
def update_room_capability():
    params = request.get_json()
    room_id = params.get('roomId')
    capability = params.get('capability')
    if not room_id or not capability:
        raise BadRequestError('Both "name" and "capability" parameters are required.')
    room = Room.update_capability(room_id, capability)
    return tolerant_jsonify(room.to_api_json())
