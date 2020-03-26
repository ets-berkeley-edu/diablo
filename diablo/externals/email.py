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

from diablo.lib.berkeley import term_name_for_sis_id
from flask import current_app as app


def send_test_email(email_template, recipient, course, recording_type_name=None, extra_key_value_pairs=None):
    message = email_template.message
    replacements = _get_replacements(
        recipient=recipient,
        course=course,
        recording_type_name=recording_type_name,
        extra_key_value_pairs=extra_key_value_pairs,
    )
    for token, value in replacements.items():
        message = message.replace(f'<code>{token}</code>', value)
    app.logger.info(message)


def get_email_template_codes():
    return list(_get_replacements().keys())


def _get_replacements(recipient=None, course=None, recording_type_name=None, extra_key_value_pairs=None):
    term_id = (course and course['termId']) or app.config['CURRENT_TERM_ID']
    return {
        **{
            'course.days': course and course['meetingDays'],
            'course.time.end': course and course['meetingEndTime'],
            'course.format': course and course['instructionFormat'],
            'course.name': course and course['courseName'],
            'course.room': course and course['meetingLocation'],
            'course.section': course and course['sectionNum'],
            'course.time.start': course and course['meetingStartTime'],
            'course.title': course and course['courseTitle'],
            'diablo.approve.url': course and _get_sign_up_url(term_id, course['sectionId']),
            'recording.type': recording_type_name,
            'term.name': term_name_for_sis_id(term_id),
            'user.name': recipient and recipient.name,
        },
        **(extra_key_value_pairs or {}),
    }


def _get_sign_up_url(term_id, section_id):
    return f'https://diablo-TODO.berkeley.edu/approve/{term_id}/{section_id}'
