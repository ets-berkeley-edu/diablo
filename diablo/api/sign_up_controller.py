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
from diablo.lib.http import tolerant_jsonify
from diablo.merged.sis import get_section
from diablo.models.sign_up import get_all_publish_types, get_all_recording_types, PUBLISH_TYPE_NAMES_PER_ID, SignUp
from flask import current_app as app, request
from flask_login import current_user, login_required


@app.route('/api/sign_up', methods=['POST'])
@login_required
def course_capture_sign_up():
    term_id = app.config['CURRENT_TERM']
    params = request.get_json()

    publish_type = params.get('publishType')
    recording_type = params.get('recordingType')
    section_id = params.get('sectionId')
    section = get_section(term_id, section_id) if section_id else None
    uid = current_user.get_uid()

    if not section or publish_type not in get_all_publish_types() or recording_type not in get_all_recording_types():
        raise BadRequestError(f'One or more required params are missing or invalid')

    if not current_user.is_admin and uid not in [i['uid'] for i in section['instructors']]:
        raise ForbiddenRequestError('Sorry, request unauthorized')

    sign_up = SignUp.get_sign_up(term_id, section_id)
    if sign_up:
        if sign_up.recordings_scheduled_at:
            raise BadRequestError(f'Recordings have already been scheduled for course {section_id}')
        if current_user.is_admin:
            if sign_up.admin_approval_uid:
                raise BadRequestError(f'Already approved by Diablo Admin user {sign_up.admin_approval_uid}')
            SignUp.set_admin_approval_uid(
                term_id,
                section_id,
                uid,
                publish_type_=publish_type,
                recording_type_=recording_type,
            )
        else:
            if uid in (sign_up.instructor_approval_uids or []):
                raise BadRequestError(f'You have already approved recordings for course {section_id}')
            SignUp.add_instructor_approval(
                term_id,
                section_id,
                uid,
                publish_type_=publish_type,
                recording_type_=recording_type,
            )
        sign_up = SignUp.get_sign_up(term_id=term_id, section_id=section_id)

    else:
        sign_up = SignUp.create(
            term_id=term_id,
            section_id=section_id,
            admin_approval_uid=uid if current_user.is_admin else None,
            instructor_approval_uid=None if current_user.is_admin else uid,
            publish_type_=publish_type,
            recording_type_=recording_type,
        )

    return tolerant_jsonify(sign_up.to_api_json())


@app.route('/api/sign_up/status/<term_id>/<section_id>')
@login_required
def sign_up_status(term_id, section_id):
    section = get_section(term_id, section_id)
    if not section:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')
    instructor_uids = [i['uid'] for i in section['instructors']]
    if not current_user.is_admin and current_user.get_uid() not in instructor_uids:
        raise ForbiddenRequestError('Sorry, this request is unauthorized.')

    sign_up = SignUp.get_sign_up(term_id, section_id)
    if sign_up:
        status = sign_up.to_api_json()
        status.pop('sectionId')
        status.pop('termId')
    else:
        status = None
    publish_type_options = []
    for value, text in PUBLISH_TYPE_NAMES_PER_ID.items():
        publish_type_options.append({
            'text': text,
            'value': value,
        })
    return tolerant_jsonify({
        'termId': term_id,
        'section': section,
        'signUpStatus': status,
        'publishTypeOptions': publish_type_options,
    })
