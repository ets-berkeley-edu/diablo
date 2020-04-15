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

import re

from diablo.externals.mailgun import Mailgun
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.models.approval import NAMES_PER_PUBLISH_TYPE, NAMES_PER_RECORDING_TYPE
from diablo.models.email_template import EmailTemplate
from flask import current_app as app


def notify_instructors_of_approval(
        course,
        latest_approval,
        name_of_latest_approver,
        template_type,
        term_id,
        pending_instructors=None,
        notify_only_latest_instructor=False,
        previous_publish_type=None,
        previous_recording_type=None,
):
    template = EmailTemplate.get_template_by_type(template_type)
    if template:
        def _interpolate(templated_string):
            return interpolate_email_content(
                course=course,
                instructor_name=name_of_latest_approver,
                pending_instructors=pending_instructors,
                previous_publish_type_name=NAMES_PER_PUBLISH_TYPE.get(previous_publish_type),
                previous_recording_type_name=NAMES_PER_RECORDING_TYPE.get(previous_recording_type),
                publish_type_name=NAMES_PER_PUBLISH_TYPE.get(latest_approval.publish_type),
                recording_type_name=NAMES_PER_RECORDING_TYPE.get(latest_approval.recording_type),
                templated_string=templated_string,
            )
        if notify_only_latest_instructor:
            recipients = [next((i for i in course['instructors'] if i['uid'] == latest_approval.uid))]
        else:
            recipients = course['instructors']
        Mailgun().send(
            message=_interpolate(template.message),
            recipients=recipients,
            section_id=course['sectionId'],
            subject_line=_interpolate(template.subject_line),
            template_type=template_type,
            term_id=term_id,
        )
        return True
    else:
        send_system_error_email(f'Unable to send email of type {template_type} because no template is available.')
        return False


def interpolate_email_content(
        templated_string,
        course=None,
        instructor_name=None,
        pending_instructors=None,
        previous_publish_type_name=None,
        previous_recording_type_name=None,
        publish_type_name=None,
        recipient_name=None,
        recording_type_name=None,
):
    interpolated = templated_string
    substitutions = _get_substitutions(
        course=course,
        instructor_name=instructor_name,
        pending_instructors=pending_instructors,
        previous_publish_type_name=previous_publish_type_name,
        previous_recording_type_name=previous_recording_type_name,
        publish_type_name=publish_type_name,
        recipient_name=recipient_name,
        recording_type_name=recording_type_name,
    )
    for token, value in substitutions.items():
        if value is not None:
            value = ','.join(value) if type(value) == list else value
            interpolated = re.sub(f'<code>[ \n\t]*{token}[ \n\t]*</code>', value, interpolated)
    return interpolated


def get_email_template_codes():
    return list(_get_substitutions().keys())


def get_admin_alert_recipients():
    return [
        {
            'email': app.config['EMAIL_DIABLO_ADMIN'],
            'name': 'Course Capture Admin',
            'uid': app.config['EMAIL_DIABLO_ADMIN_UID'],
        },
    ]


def send_invite_related_email(
        course,
        template_type,
        term_id,
):
    template = EmailTemplate.get_template_by_type(template_type)
    if template:
        def _interpolate(templated_string):
            return interpolate_email_content(
                course=course,
                templated_string=templated_string,
            )
        Mailgun().send(
            message=_interpolate(template.message),
            recipients=course['instructors'],
            section_id=course['sectionId'],
            subject_line=_interpolate(template.subject_line),
            template_type=template_type,
            term_id=term_id,
        )
        return True
    else:
        send_system_error_email(f'Unable to send email of type {template_type} because no template is available.')
        return False


def send_system_error_email(message):
    subject = f'{message[:50]}...' if len(message) > 50 else message
    Mailgun().send(
        message=message,
        recipients=get_admin_alert_recipients(),
        subject_line=f'Diablo Alert: {subject}',
    )
    app.logger.error(f'Diablo Alert: {message}')


def _get_substitutions(
        course=None,
        instructor_name=None,
        pending_instructors=None,
        previous_publish_type_name=None,
        previous_recording_type_name=None,
        publish_type_name=None,
        recipient_name=None,
        recording_type_name=None,
):
    term_id = (course and course['termId']) or app.config['CURRENT_TERM_ID']
    return {
        'course.days': course and course['meetingDays'],
        'course.format': course and course['instructionFormat'],
        'course.name': course and course['courseName'],
        'course.room': course and course['meetingLocation'],
        'course.section': course and course['sectionNum'],
        'course.time.end': course and course['meetingEndTime'],
        'course.time.start': course and course['meetingStartTime'],
        'course.title': course and course['courseTitle'],
        'instructor.name': instructor_name,
        'instructors.pending': pending_instructors and [p['name'] for p in pending_instructors],
        'publish.type': publish_type_name,
        'publish.type.previous': previous_publish_type_name,
        'recording.type': recording_type_name,
        'recording.type.previous': previous_recording_type_name,
        'signup.url': course and _get_sign_up_url(term_id, course['sectionId']),
        'term.name': term_name_for_sis_id(term_id),
        'user.name': recipient_name,
    }


def _get_sign_up_url(term_id, section_id):
    return f'https://diablo-TODO.berkeley.edu/approve/{term_id}/{section_id}'
