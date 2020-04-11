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
import os

from tests.test_jobs.sample_jobs import HelloWorld, LightSwitch

# Base directory for the application (one level up from this config file).
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

ALERT_INFREQUENT_ACTIVITY_ENABLED = False
ALERT_WITHDRAWAL_ENABLED = False

CURRENT_TERM_ID = 2202

DATA_LOCH_RDS_URI = 'postgres://diablo:diablo@localhost:5432/pazuzu_loch_test'

JOB_MANAGER = {
    'auto_start': True,
    'seconds_between_pending_jobs_check': 60,
    'jobs': [
        {
            'cls': HelloWorld,
            'schedule': {
                'type': 'seconds',
                'value': 300,
            },
        },
        {
            'cls': LightSwitch,
            'disabled': True,
            'schedule': {
                'type': 'day_at',
                'value': '06:00',
            },
        },
    ],
}

INDEX_HTML = f'{BASE_DIR}/tests/static/test-index.html'

LOGGING_LOCATION = 'STDOUT'

SQLALCHEMY_DATABASE_URI = 'postgres://diablo:diablo@localhost:5432/pazuzu_test'

TESTING = True
