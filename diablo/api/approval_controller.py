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

from diablo.api.errors import BadRequestError, ForbiddenRequestError, ResourceNotFoundError
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.http import tolerant_jsonify
from diablo.merged.sis import get_section
from diablo.models.approval import Approval, get_all_publish_types, get_all_recording_types, PUBLISH_TYPE_NAMES_PER_ID
from diablo.models.room import Room
from flask import current_app as app, request
from flask_login import current_user, login_required


@app.route('/api/approve', methods=['POST'])
@login_required
def course_capture_sign_up():
    approved_by_uid = current_user.get_uid()
    term_id = app.config['CURRENT_TERM']
    term_name = term_name_for_sis_id(term_id)

    params = request.get_json()
    publish_type = params.get('publishType')
    recording_type = params.get('recordingType')
    section_id = params.get('sectionId')
    section = get_section(term_id, section_id) if section_id else None

    if not section or publish_type not in get_all_publish_types() or recording_type not in get_all_recording_types():
        raise BadRequestError(f'One or more required params are missing or invalid')

    if not current_user.is_admin and approved_by_uid not in [i['uid'] for i in section['instructors']]:
        raise ForbiddenRequestError('Sorry, request unauthorized')

    if Approval.get_approval(approved_by_uid, section_id, term_id):
        raise ForbiddenRequestError(f'You have already approved recording of {section["courseName"]}, {term_name}')

    room = Room.create_or_update(
        location=section['room']['location'],
        capabilities=[s['value'] for s in section['room']['capabilities']],
    )
    Approval.create(
        approved_by_uid=approved_by_uid,
        section_id=section_id,
        term_id=term_id,
        approver_type_='admin' if current_user.is_admin else 'instructor',
        location=room.location,
        publish_type_=publish_type,
        recording_type_=recording_type,
    )

    return tolerant_jsonify(_all_approvals_to_json(section, term_id))


@app.route('/api/approvals/<term_id>/<section_id>')
@login_required
def approvals(term_id, section_id):
    section = get_section(term_id, section_id)
    if not section:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')
    instructor_uids = [i['uid'] for i in section['instructors']]
    if not current_user.is_admin and current_user.get_uid() not in instructor_uids:
        raise ForbiddenRequestError('Sorry, this request is unauthorized.')
    return tolerant_jsonify(_all_approvals_to_json(section, term_id))


def _all_approvals_to_json(section, term_id):
    return {
        'termId': term_id,
        'section': section,
        'approvals': [approval.to_api_json() for approval in Approval.get_approvals(section['sectionId'], term_id)],
        'publishTypeOptions': [{'text': text, 'value': value} for value, text in PUBLISH_TYPE_NAMES_PER_ID.items()],
    }
