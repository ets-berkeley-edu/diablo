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

import time

from diablo.jobs.background_job_manager import BackgroundJobManager
from flask import current_app as app
from tests.test_jobs.sample_jobs import HelloWorld, LightSwitch, Volume, VolumeSubClass
from tests.util import override_config


class TestBackgroundJobManager:

    def test_start_mock_jobs(self):
        """Runs jobs as scheduled and skips disabled jobs."""
        with override_config(app, 'JOB_MANAGER', _job_manager_config()):
            job_manager = BackgroundJobManager()
            try:
                job_manager.start(app)
                # The JOB_MANAGER config has four (4) jobs but one is disabled. So, only three are loaded.
                assert len(job_manager.job_instances) == 3
                time.sleep(2)

                for job_instance in job_manager.job_instances:
                    if job_instance.key() == 'volume':
                        assert job_instance.level == 11
                    elif job_instance.key() == 'volume_sub_class':
                        # Property not yet set
                        assert job_instance.level is None
                    elif job_instance.key() == 'light_switch':
                        assert job_instance.is_light_on is True
                    else:
                        assert False

            finally:
                job_manager.stop()


def _job_manager_config():
    return {
        'auto_start': False,
        'seconds_between_pending_jobs_check': 0.5,
        'jobs': [
            {
                'cls': Volume,
                'schedule': {
                    'type': 'seconds',
                    'value': 1,
                },
            },
            {
                'cls': VolumeSubClass,
                'schedule': {
                    'type': 'day_at',
                    'value': '04:30',
                },
            },
            {
                'cls': HelloWorld,
                'disabled': True,
                'schedule': {
                    'type': 'seconds',
                    'value': 1,
                },
            },
            {
                'cls': LightSwitch,
                'schedule': {
                    'type': 'seconds',
                    'value': 1,
                },
            },
        ],
    }
