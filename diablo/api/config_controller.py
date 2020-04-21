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

import json

from diablo import __version__ as version
from diablo.api.util import get_search_filter_options
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.http import tolerant_jsonify
from diablo.models.email_template import EmailTemplate
from diablo.models.room import Room
from flask import current_app as app


@app.route('/api/config')
def app_config():
    term_id = app.config['CURRENT_TERM_ID']
    return tolerant_jsonify({
        'canvasBaseUrl': app.config['CANVAS_BASE_URL'],
        'courseCaptureExplainedUrl': app.config['COURSE_CAPTURE_EXPLAINED_URL'],
        'courseCapturePoliciesUrl': app.config['COURSE_CAPTURE_POLICIES_URL'],
        'currentTermId': term_id,
        'currentTermName': term_name_for_sis_id(term_id),
        'devAuthEnabled': app.config['DEVELOPER_AUTH_ENABLED'],
        'diabloEnv': app.config['DIABLO_ENV'],
        'ebEnvironment': app.config['EB_ENVIRONMENT'] if 'EB_ENVIRONMENT' in app.config else None,
        'emailTemplateTypes': EmailTemplate.get_template_type_options(),
        'searchItemsPerPage': app.config['SEARCH_ITEMS_PER_PAGE'],
        'roomCapabilityOptions': Room.get_room_capability_options(),
        'searchFilterOptions': get_search_filter_options(),
        'supportEmailAddress': app.config['EMAIL_DIABLO_SUPPORT'],
        'timezone': app.config['TIMEZONE'],
    })


@app.route('/api/version')
def app_version():
    v = {
        'version': version,
    }
    build_stats = load_json('config/build-summary.json')
    if build_stats:
        v.update(build_stats)
    else:
        v.update({
            'build': None,
        })
    return tolerant_jsonify(v)


def load_json(relative_path):
    try:
        file = open(app.config['BASE_DIR'] + '/' + relative_path)
        return json.load(file)
    except (FileNotFoundError, KeyError, TypeError):
        return None
