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
import logging
import os

# Base directory for the application (one level up from this config file).
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# bConnected On-Premise (bCOP) SMTP server
BCOP_SMTP_PASSWORD = None
BCOP_SMTP_PORT = 587
BCOP_SMTP_SERVER = 'bcop.berkeley.edu'
BCOP_SMTP_USERNAME = None

CACHE_DEFAULT_TIMEOUT = 86400
CACHE_DIR = f'{BASE_DIR}/.flask_cache'
CACHE_THRESHOLD = 300
CACHE_TYPE = 'filesystem'

CANVAS_ACCESS_TOKEN = 'a token'
CANVAS_API_URL = 'https://hard_knocks_api.instructure.com'
CANVAS_BASE_URL = 'https://ucberkeley.foo.instructure.com'
CANVAS_BERKELEY_ACCOUNT_ID = 00000
CANVAS_BERKELEY_SUB_ACCOUNTS = [00000]
CANVAS_ENROLLMENT_TERM_ID = 0000

CANVAS_LTI_EXTERNAL_TOOL_IDS = {
    'media_gallery': 1,
    'my_media': 2,
    'quick_ingest': 3,
    'video_submission': 4,
}
CANVAS_LTI_KEY = 'a_key'
CANVAS_LTI_SECRET = 'a_secret'

CAS_SERVER = 'https://auth-test.berkeley.edu/cas/'

COURSE_CAPTURE_EXPLAINED_URL = 'https://www.ets.berkeley.edu/services-facilities/course-capture'
COURSE_CAPTURE_POLICIES_URL = 'https://www.ets.berkeley.edu/services-facilities/course-capture/course-capture-instructors-getting-started/policies'

# TODO: Remove when Summer 2020 pilot is done
COURSE_CAPTURE_PILOT_JSON = f'{BASE_DIR}/config/course_capture_pilot.json'
COURSE_CAPTURE_PREMIUM_COST = 2000

# YYYY-MM-DD is expected date format. For example, '2020-01-21'
CURRENT_TERM_BEGIN = None
CURRENT_TERM_END = None
CURRENT_TERM_ID = None
CURRENT_TERM_RECORDINGS_BEGIN = None
CURRENT_TERM_RECORDINGS_END = None

DEV_AUTH_ENABLED = False
DEV_AUTH_PASSWORD = 'another secret'

DIABLO_BASE_URL = 'https://manage-foo.coursecapture.berkeley.edu'

EASTER_EGG_420 = 'https://www.youtube.com/watch?v=JS9hjJJ9nWc'

EMAIL_COURSE_CAPTURE_SUPPORT = '__EMAIL_COURSE_CAPTURE_SUPPORT__at_berkeley.edu'
EMAIL_COURSE_CAPTURE_SUPPORT_LABEL = 'Course Capture Admin'
EMAIL_DIABLO_ADMIN = '__EMAIL_DIABLO_ADMIN__at_berkeley.edu'
EMAIL_DIABLO_ADMIN_UID = '0'
EMAIL_IF_PING_HAS_ERROR = True
EMAIL_REDIRECT_WHEN_TESTING = ['__EMAIL_REDIRECT_WHEN_TESTING__at_berkeley.edu']
EMAIL_SYSTEM_ERRORS = ['__EMAIL_SYSTEM_ERRORS__at_berkeley.edu']
EMAIL_TEST_MODE = True

# Useful when working on or debugging the Kaltura integration. Recommended for localhost only.
FEATURE_FLAG_SCHEDULE_RECORDINGS_SYNCHRONOUSLY = False

# Directory to search for mock fixtures, if running in "test" or "demo" mode.
FIXTURES_PATH = None

# background_job_manager configs.
JOB_HISTORY_DAYS_UNTIL_EXPIRE = 7
JOBS_AUTO_START = False
JOBS_SECONDS_BETWEEN_PENDING_CHECK = 60

# Minutes of inactivity before session cookie is destroyed
INACTIVE_SESSION_LIFETIME = 20

# These "INDEX_HTML" defaults are good in diablo-[dev|qa|prod]. See development.py for local configs.
INDEX_HTML = 'dist/static/index.html'

KALTURA_ADMIN_SECRET = 'secret'
KALTURA_BLACKOUT_DATES = ['2020-09-07', '2020-11-11', '2020-11-25', '2020-11-26', '2020-11-27']
KALTURA_EVENT_ORGANIZER = '____at_berkeley.edu'
KALTURA_EXPIRY = 0
KALTURA_KMS_OWNER_ID = 'owner_id'
KALTURA_MEDIA_SPACE_URL = 'https://____.mediaspace.kaltura.com'
KALTURA_PARTNER_ID = '0000000'
KALTURA_RECORDING_OFFSET_END = 2
KALTURA_RECORDING_OFFSET_START = 7
KALTURA_UNIQUE_USER_ID = 'user_id'

LDAP_HOST = 'ldap-test.berkeley.edu'
LDAP_BIND = 'mybind'
LDAP_PASSWORD = 'secret'

# Logging
LOGGING_FORMAT = '[%(asctime)s] - %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
LOGGING_LOCATION = 'diablo.log'
LOGGING_LEVEL = logging.DEBUG
LOGGING_PROPAGATION_LEVEL = logging.WARN

REDSHIFT_DATABASE = '__nessie__'
REDSHIFT_SCHEMA_SIS = '__sis_data_ext__'

REMEMBER_COOKIE_NAME = 'remember_diablo_token'

SEARCH_ITEMS_PER_PAGE = 50

# Used to encrypt session cookie.
SECRET_KEY = 'secret'

# SQLAlchemy
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_DATABASE_URI = 'postgres://diablo:diablo@localhost:5432/pazuzu'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# A common configuration; one request thread, one background worker thread.
THREADS_PER_PAGE = 2

TIMEZONE = 'America/Los_Angeles'

# This base-URL config should only be non-None in the "local" env where the Vue front-end runs on port 8080.
VUE_LOCALHOST_BASE_URL = None

XENA_EMAIL_USERNAME = 'xena@amphipolis.gov'
XENA_EMAIL_PASSWORD = 'shhh'
XENA_EMAIL_DELIVERY_RETRIES = 15
XENA_KALTURA_USERNAME = 'some-user-name@domain.com'
XENA_KALTURA_PASSWORD = 'some-complicated-string'

# We keep these out of alphabetical sort above for readability's sake.
HOST = '0.0.0.0'
PORT = 5000
