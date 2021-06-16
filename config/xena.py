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

import logging
import os

ADMIN_UID = '1049291'

# Base directory for the application (one level up from this config file).
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = 'https://manage-dev.coursecapture.berkeley.edu'

CANVAS_ADMIN_ID = '123456'
CANVAS_BASE_URL = 'https://ucberkeley.beta.instructure.com'
CANVAS_ROOT_ACCOUNT = '123456'
CANVAS_SITE_CREATION_TOOL = '654321'
CANVAS_MEDIA_GALLERY_TOOL = '13579'
CANVAS_MY_MEDIA_TOOL = '24680'

CLICK_SLEEP = 0.5

CURRENT_TERM_NAME = 'Fall 2021'

INDEX_HTML = f'{BASE_DIR}/tests/static/test-index.html'

JUNCTION_BASE_URL = 'https://junction-dev.berkeley.edu'

KALTURA_TOOL_URL = 'https://kaltura.tool.url'
KALTURA_BLACKOUT_DATES = []

LOGGING_LEVEL = logging.INFO

TESTING = True

TEST_DATA_ROOMS = f'{BASE_DIR}/xena/fixtures/test-rooms.json'

# The test-courses.json file is intended as an example of required structure of the test data
TEST_DATA_COURSES = f'{BASE_DIR}/xena/fixtures/test-courses-local.json'

TIMEOUT_SHORT = 10
TIMEOUT_MEDIUM = 90
TIMEOUT_LONG = 360

XENA_BROWSER = 'firefox'
