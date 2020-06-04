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

from canvasapi import Canvas
from diablo import skip_when_pytest
from flask import current_app as app


@skip_when_pytest(mock_object='canvas/canvas_course_sites.json', is_fixture_json_file=True)
def get_canvas_course_sites(canvas_enrollment_term_id):
    canvas_courses = _get_canvas().get_courses(
        by_subaccounts=app.config['CANVAS_BERKELEY_SUB_ACCOUNTS'],
        enrollment_term_id=canvas_enrollment_term_id,
        published=True,
        with_enrollments=True,
    )
    canvas_course_sites = {}
    # Sample formats: 'SEC:2020-B-21662', 'SEC:2020-B-21662-9F6ED069'
    sis_section_regex = re.compile(r'SEC:\d+-\D-(\d+).*')
    for canvas_course in canvas_courses:
        for section in canvas_course.get_sections():
            course_site_id = section.course_id
            sis_section_id = section.sis_section_id
            section_id = sis_section_regex.search(sis_section_id).group(1) if sis_section_id else None
            if section_id:
                if course_site_id not in canvas_course_sites:
                    canvas_course_sites[course_site_id] = {
                        'section_ids': [],
                        'canvas_course_site_name': canvas_course.name,
                    }
                canvas_course_sites[course_site_id]['section_ids'].append(section_id)
    return canvas_course_sites


def ping_canvas():
    return _get_canvas() is not None


def _get_canvas():
    canvas = Canvas(
        base_url=app.config['CANVAS_API_URL'],
        access_token=app.config['CANVAS_ACCESS_TOKEN'],
    )
    return canvas.get_account(app.config['CANVAS_BERKELEY_ACCOUNT_ID'])
