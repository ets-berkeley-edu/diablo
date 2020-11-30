"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.externals.b_connected import BConnected
from diablo.lib.http import tolerant_jsonify
from diablo.lib.interpolator import get_template_substitutions, interpolate_content
from diablo.models.approval import get_all_publish_types, get_all_recording_types, NAMES_PER_PUBLISH_TYPE, \
    NAMES_PER_RECORDING_TYPE
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import QueuedEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app, request
from flask_login import current_user


@app.route('/api/email/templates/all')
@admin_required
def get_all_email_templates():
    return tolerant_jsonify([template.to_api_json() for template in EmailTemplate.all_templates()])


@app.route('/api/email/template/<template_id>')
@admin_required
def get_email_template(template_id):
    email_template = EmailTemplate.get_template(template_id)
    if email_template:
        return tolerant_jsonify(email_template.to_api_json())
    else:
        raise ResourceNotFoundError('No such email_template')


@app.route('/api/email/template/delete/<template_id>', methods=['DELETE'])
@admin_required
def delete_email_template(template_id):
    EmailTemplate.delete_template(template_id)
    return tolerant_jsonify({'message': f'Email template {template_id} has been deleted'}), 200


@app.route('/api/email/template/codes')
@admin_required
def get_template_codes():
    template_codes = list(get_template_substitutions(course=None, recipient_name=None).keys())
    return tolerant_jsonify(template_codes)


@app.route('/api/email/template/create', methods=['POST'])
@admin_required
def create():
    params = request.get_json()
    template_type = params.get('templateType')
    name = params.get('name')
    subject_line = params.get('subjectLine')
    message = params.get('message')

    if None in [template_type, name, subject_line, message]:
        raise BadRequestError('Required parameters are missing.')

    email_template = EmailTemplate.create(
        template_type=template_type,
        name=name,
        subject_line=subject_line,
        message=message,
    )
    return tolerant_jsonify(email_template.to_api_json())


@app.route('/api/email/template/test/<template_id>')
@admin_required
def test_email_template(template_id):
    email_template = EmailTemplate.get_template(template_id)
    if email_template:
        course = SisSection.get_random_co_taught_course(app.config['CURRENT_TERM_ID'])
        template = EmailTemplate.get_template(template_id)
        publish_types = get_all_publish_types()
        recording_types = get_all_recording_types()

        def _get_interpolated_content(templated_string):
            return interpolate_content(
                course=course,
                pending_instructors=course['instructors'],
                previous_publish_type_name=NAMES_PER_PUBLISH_TYPE[publish_types[0]],
                previous_recording_type_name=NAMES_PER_RECORDING_TYPE[recording_types[0]],
                publish_type_name=NAMES_PER_PUBLISH_TYPE[publish_types[1]],
                recording_type_name=NAMES_PER_RECORDING_TYPE[recording_types[1]],
                recipient_name=current_user.name,
                templated_string=templated_string,
            )
        BConnected().send(
            recipient={
                'email': current_user.email_address,
                'name': current_user.name,
                'uid': current_user.uid,
            },
            message=_get_interpolated_content(template.message),
            subject_line=_get_interpolated_content(template.subject_line),
        )
        return tolerant_jsonify({'message': f'Email sent to {current_user.email_address}'}), 200
    else:
        raise ResourceNotFoundError('No such email_template')


@app.route('/api/email/template/update', methods=['POST'])
@admin_required
def update():
    params = request.get_json()
    template_id = params.get('templateId')
    email_template = EmailTemplate.get_template(template_id) if template_id else None
    if email_template:
        template_type = params.get('templateType')
        name = params.get('name')
        subject_line = params.get('subjectLine')
        message = params.get('message')

        if None in [template_type, name, subject_line, message]:
            raise BadRequestError('Required parameters are missing.')

        email_template = EmailTemplate.update(
            template_id=template_id,
            template_type=template_type,
            name=name,
            subject_line=subject_line,
            message=message,
        )
        return tolerant_jsonify(email_template.to_api_json())
    else:
        raise ResourceNotFoundError('No such email template')


@app.route('/api/emails/queue', methods=['POST'])
@admin_required
def queue_emails():
    params = request.get_json()
    term_id = params.get('termId')
    section_id = params.get('sectionId')
    template_type = params.get('emailTemplateType')

    if not (term_id and section_id and template_type):
        raise BadRequestError('Required parameters are missing.')
    course = SisSection.get_course(term_id=term_id, section_id=section_id)
    for instructor in course['instructors']:
        if not QueuedEmail.create(section_id=section_id, recipient=instructor, template_type=template_type, term_id=term_id):
            raise BadRequestError(f"Failed to queue email of type '{template_type}'.")
    return tolerant_jsonify({
        'message': f"An email of type '{template_type}' has been queued.",
    })
