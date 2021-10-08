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

import re

from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.util import get_names_of_days, readable_join
from flask import current_app as app


def interpolate_content(
    course,
    recipient_name,
    templated_string,
    pending_instructors=None,
    previous_publish_type_name=None,
    previous_recording_type_name=None,
    publish_type_name=None,
    recording_type_name=None,
):
    interpolated = templated_string
    substitutions = get_template_substitutions(
        course=course,
        recipient_name=recipient_name,
        pending_instructors=pending_instructors,
        previous_publish_type_name=previous_publish_type_name,
        previous_recording_type_name=previous_recording_type_name,
        publish_type_name=publish_type_name,
        recording_type_name=recording_type_name,
    )
    for token, value in substitutions.items():
        if value is None:
            value = 'None'
        elif type(value) == list:
            value = ','.join(value)
        interpolated = re.sub(f'<code>[ \n\t]*{token}[ \n\t]*</code>', value, interpolated)
    return interpolated


def get_sign_up_url(term_id, section_id):
    base_url = app.config['DIABLO_BASE_URL']
    return f'{base_url}/course/{term_id}/{section_id}'


def get_template_substitutions(
        course,
        recipient_name,
        pending_instructors=None,
        previous_publish_type_name=None,
        previous_recording_type_name=None,
        publish_type_name=None,
        recording_type_name=None,
):
    term_id = (course and course['termId']) or app.config['CURRENT_TERM_ID']

    def _join_names(_dict):
        if not _dict:
            return None
        return ', '.join(i['name'] for i in _dict if i['name'])

    if course:
        meetings = course.get('meetings', {}).get('eligible', [])
        meetings = meetings or course.get('meetings', {}).get('ineligible', [])
        meeting = meetings and meetings[0]
        days = meeting and get_names_of_days(meeting['daysFormatted'])
    else:
        days = None
        meeting = None

    return {
        'course.date.end': meeting and meeting['endDate'],
        'course.date.start': meeting and meeting['startDate'],
        'course.days': days and readable_join(days),
        'course.format': course and course['instructionFormat'],
        'course.name': course and course['courseName'],
        'course.room': 'CANCELED' if course and course['deletedAt'] else (meeting and meeting['location']),
        'course.section': course and course['sectionNum'],
        'course.time.end': meeting and meeting['endTimeFormatted'],
        'course.time.start': meeting and meeting['startTimeFormatted'],
        'course.title': course and course['courseTitle'],
        'instructors.all': course and _join_names(course.get('instructors')),
        'instructors.pending': _join_names(pending_instructors),
        'instructors.previous': course and course.get('scheduled') and _join_names(course['scheduled'].get('instructors')),
        'publish.type': publish_type_name,
        'publish.type.previous': previous_publish_type_name,
        'recipient.name': recipient_name,
        'recording.type': recording_type_name,
        'recording.type.previous': previous_recording_type_name,
        'signup.url': course and get_sign_up_url(term_id, course['sectionId']),
        'term.name': term_name_for_sis_id(term_id),
    }
