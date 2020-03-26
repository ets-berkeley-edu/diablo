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

from canvasapi import Canvas
from diablo import cachify
from flask import current_app as app


@cachify('canvas/section_ids_per_course_site_id')
def get_section_ids_per_course_site_id(canvas_enrollment_term_id):
    canvas = Canvas(
        base_url=app.config['CANVAS_API_URL'],
        access_token=app.config['CANVAS_ACCESS_TOKEN'],
    )
    account = canvas.get_account(app.config['CANVAS_BERKELEY_ACCOUNT_ID'])
    courses = account.get_courses(
        enrollment_term_id=canvas_enrollment_term_id,
        search_term='Scandinavian',
        with_enrollments=True,
    )
    section_ids_per_course_site_id = {}
    for course in courses:
        for section in course.get_sections():
            course_site_id = section.course_id
            # The 'sis_section_id' value will be similar to 'SEC:2020-B-21662'
            sis_section_id = section.sis_section_id
            if sis_section_id and 'SEC:' in sis_section_id and '-' in sis_section_id:
                section_id = int(sis_section_id.rsplit('-', 1)[1])
                if course_site_id not in section_ids_per_course_site_id:
                    section_ids_per_course_site_id[course_site_id] = []
                section_ids_per_course_site_id[course_site_id].append(section_id)
    return section_ids_per_course_site_id
