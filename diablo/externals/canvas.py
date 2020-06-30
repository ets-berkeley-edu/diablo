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
from canvasapi.external_tool import ExternalTool
from diablo import skip_when_pytest
from diablo.lib.util import resolve_xml_template
from flask import current_app as app


@skip_when_pytest(mock_object='canvas/canvas_course_sites.json', is_fixture_json_file=True)
def get_canvas_course_sites(canvas_enrollment_term_id):
    canvas_courses = _get_canvas().get_courses(
        by_subaccounts=app.config['CANVAS_BERKELEY_SUB_ACCOUNTS'],
        enrollment_term_id=canvas_enrollment_term_id,
    )
    course_sites_by_id = {}
    # Sample formats: 'SEC:2020-B-21662', 'SEC:2020-B-21662-9F6ED069'
    sis_section_regex = re.compile(r'SEC:\d+-\D-(\d+).*')
    for canvas_course in canvas_courses:
        for section in canvas_course.get_sections():
            if hasattr(section, 'course_id') and hasattr(section, 'sis_section_id'):
                course_site_id = section.course_id
                sis_section_id = section.sis_section_id
                section_id = sis_section_regex.search(sis_section_id).group(1) if sis_section_id else None
                if section_id:
                    if course_site_id not in course_sites_by_id:
                        course_sites_by_id[course_site_id] = {
                            'id': course_site_id,
                            'name': canvas_course.name,
                            'section_ids': set(),
                        }
                    course_sites_by_id[course_site_id]['section_ids'].add(section_id)
    return list(course_sites_by_id.values())


def ping_canvas():
    return _get_canvas() is not None


def update_lti_configurations():
    canvas = Canvas(
        base_url=app.config['CANVAS_API_URL'],
        access_token=app.config['CANVAS_ACCESS_TOKEN'],
    )
    successes = []
    errors = []
    for tool_name, tool_id in app.config.get('CANVAS_LTI_EXTERNAL_TOOL_IDS', {}).items():
        xml_string = resolve_xml_template(f'{tool_name}.xml')
        external_tool = ExternalTool(
            canvas._Canvas__requester,
            {
                'account_id': app.config['CANVAS_BERKELEY_ACCOUNT_ID'],
                'id': tool_id,
            },
        )
        response = None
        try:
            response = external_tool.edit(
                config_type='by_xml',
                config_xml=xml_string,
                consumer_key=app.config['CANVAS_LTI_KEY'],
                shared_secret=app.config['CANVAS_LTI_SECRET'],
            )
        except Exception as e:
            app.logger.error(f'Failed to update external tool {tool_name} due to error: {str(e)}')
            app.logger.exception(e)
        if response and response.name:
            successes.append(response.name)
        else:
            errors.append(tool_name)
    return successes, errors


def _get_canvas():
    canvas = Canvas(
        base_url=app.config['CANVAS_API_URL'],
        access_token=app.config['CANVAS_ACCESS_TOKEN'],
    )
    return canvas.get_account(app.config['CANVAS_BERKELEY_ACCOUNT_ID'])
