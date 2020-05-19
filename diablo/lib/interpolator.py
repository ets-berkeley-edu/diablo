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

from diablo.lib.berkeley import term_name_for_sis_id
from flask import current_app as app


def interpolate_content(
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
    substitutions = get_template_substitutions(
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


def get_template_substitutions(
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
    diablo_env = app.config['DIABLO_ENV']
    sub_domain = 'manage' if diablo_env == 'production' else f'manage-{diablo_env}'
    return f'https://{sub_domain}.coursecapture.berkeley.edu/course/{term_id}/{section_id}'
