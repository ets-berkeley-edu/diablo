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
from diablo.api.util import admin_required
from diablo.lib.berkeley import get_instructor_uids, has_necessary_approvals, term_name_for_sis_id
from diablo.lib.http import tolerant_jsonify
from diablo.merged.sis import get_courses_per_section_ids, get_section
from diablo.models.approval import Approval, get_all_publish_types, get_all_recording_types, PUBLISH_TYPE_NAMES_PER_ID
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from flask import current_app as app, request
from flask_login import current_user, login_required


@app.route('/api/course/approve', methods=['POST'])
@login_required
def approve():
    approved_by_uid = current_user.get_uid()
    term_id = app.config['CURRENT_TERM_ID']
    term_name = term_name_for_sis_id(term_id)

    params = request.get_json()
    publish_type = params.get('publishType')
    recording_type = params.get('recordingType')
    section_id = params.get('sectionId')
    section = get_section(term_id, section_id) if section_id else None

    if not section or publish_type not in get_all_publish_types() or recording_type not in get_all_recording_types():
        raise BadRequestError('One or more required params are missing or invalid')

    if not current_user.is_admin and approved_by_uid not in [i['uid'] for i in section['instructors']]:
        raise ForbiddenRequestError('Sorry, request unauthorized')

    if Approval.get_approval(approved_by_uid, section_id, term_id):
        raise ForbiddenRequestError(f'You have already approved recording of {section["courseName"]}, {term_name}')

    location = section['meetingLocation']
    room = Room.find_room(location=location)
    if not room:
        raise BadRequestError(f'{location} is not eligible for Course Capture.')

    Approval.create(
        approved_by_uid=approved_by_uid,
        section_id=section_id,
        term_id=term_id,
        approver_type_='admin' if current_user.is_admin else 'instructor',
        publish_type_=publish_type,
        recording_type_=recording_type,
        room_id=room.id,
    )
    return tolerant_jsonify(_course_to_json(section, term_id))


@app.route('/api/course/approvals/<term_id>/<section_id>')
@login_required
def get_approvals(term_id, section_id):
    section = get_section(term_id, section_id)
    if not section:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')

    if not current_user.is_admin and current_user.get_uid() not in get_instructor_uids(section):
        raise ForbiddenRequestError('Sorry, this request is unauthorized.')
    return tolerant_jsonify(_course_to_json(section, term_id))


@app.route('/api/courses/approvals/<term_id>')
@admin_required
def approvals_per_term(term_id):
    return tolerant_jsonify(_approvals_per_section(term_id))


@app.route('/api/courses/term/<term_id>')
@admin_required
def term_report(term_id):
    def _objects_per_section_id(objects):
        per_section_id = {}
        for obj in objects:
            key = str(obj.section_id)
            if obj.section_id not in per_section_id:
                per_section_id[key] = []
            per_section_id[key].append(obj.to_api_json())
        return per_section_id

    api_json = []
    approvals_per_section_id = _objects_per_section_id(Approval.get_approvals_per_term(term_id))
    scheduled_per_section_id = _objects_per_section_id(Scheduled.get_all_scheduled(term_id))
    section_ids = set(approvals_per_section_id.keys()).union(set(scheduled_per_section_id.keys()))

    for section in get_courses_per_section_ids(term_id, section_ids):
        section_id = section['sectionId']
        section['approvals'] = approvals_per_section_id.get(section_id, [])
        room = Room.find_room(section['meetingLocation'])
        section['room'] = room and room.to_api_json()
        section['scheduled'] = scheduled_per_section_id.get(section_id, [])
        api_json.append(section)
    return tolerant_jsonify(api_json)


def _course_to_json(section, term_id):
    room = Room.find_room(section['meetingLocation'])
    section_id = section['sectionId']
    all_approvals = Approval.get_approvals_per_section_id(section_id, term_id)
    return {
        'approvals': [approval.to_api_json() for approval in all_approvals],
        'hasNecessaryApprovals': has_necessary_approvals(section, all_approvals),
        'publishTypeOptions': PUBLISH_TYPE_NAMES_PER_ID,
        'room': room.to_api_json(),
        'scheduled': Scheduled.was_scheduled(section_id=section_id, term_id=term_id),
        'section': section,
        'termId': term_id,
    }


def _approvals_per_section(term_id):
    approvals_per_section_id = {}
    for approval in Approval.get_approvals_per_term(term_id):
        section_id = approval.section_id
        if section_id not in approvals_per_section_id:
            approvals_per_section_id[section_id] = []
        approvals_per_section_id[section_id].append(approval.to_api_json())

    api_json = []
    section_ids = list(approvals_per_section_id.keys())
    for section in get_courses_per_section_ids(term_id, section_ids):
        section_id = section['sectionId']
        section['approvals'] = approvals_per_section_id[section_id] if section_id in approvals_per_section_id else []
        api_json.append(section)
    return api_json