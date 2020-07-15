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
from diablo.lib.util import get_eb_environment
from diablo.models.approval import NAMES_PER_PUBLISH_TYPE
from diablo.models.email_template import EmailTemplate
from diablo.models.room import Room
from flask import current_app as app

PUBLIC_CONFIGS = [
    'CANVAS_BASE_URL',
    'COURSE_CAPTURE_EXPLAINED_URL',
    'COURSE_CAPTURE_POLICIES_URL',
    'COURSE_CAPTURE_PREMIUM_COST',
    'CURRENT_TERM_BEGIN',
    'CURRENT_TERM_END',
    'CURRENT_TERM_ID',
    'CURRENT_TERM_RECORDINGS_BEGIN',
    'CURRENT_TERM_RECORDINGS_END',
    'DEV_AUTH_ENABLED',
    'DIABLO_BASE_URL',
    'DIABLO_ENV',
    'EMAIL_COURSE_CAPTURE_SUPPORT',
    'EMAIL_DIABLO_ADMIN',
    'EMAIL_REDIRECT_WHEN_TESTING',
    'EMAIL_SYSTEM_ERRORS',
    'EMAIL_TEST_MODE',
    'KALTURA_BLACKOUT_DATES',
    'KALTURA_EVENT_ORGANIZER',
    'KALTURA_MEDIA_SPACE_URL',
    'SEARCH_ITEMS_PER_PAGE',
    'TIMEZONE',
]


@app.route('/api/config')
def app_config():
    def _to_api_key(key):
        chunks = key.split('_')
        return f"{chunks[0].lower()}{''.join(chunk.title() for chunk in chunks[1:])}"
    return tolerant_jsonify(
        {
            **dict((_to_api_key(key), app.config[key]) for key in PUBLIC_CONFIGS),
            **{
                'currentTermName': term_name_for_sis_id(app.config['CURRENT_TERM_ID']),
                'ebEnvironment': get_eb_environment(),
                'emailTemplateTypes': EmailTemplate.get_template_type_options(),
                'publishTypeOptions': NAMES_PER_PUBLISH_TYPE,
                'roomCapabilityOptions': Room.get_room_capability_options(),
                'searchFilterOptions': get_search_filter_options(),
            },
        },
    )


@app.route('/api/version')
def app_version():
    v = {
        'version': version,
        'devil': ' Ψ(•̀ᴗ•́)و ',
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
