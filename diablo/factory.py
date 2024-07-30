"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

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

from diablo import cache, db
from diablo.configs import load_configs
from diablo.jobs.background_job_manager import BackgroundJobManager
from diablo.logger import initialize_logger
from diablo.routes import register_routes
from flask import Flask

background_job_manager = BackgroundJobManager()


def create_app(standalone=False):
    """Initialize app with configs."""
    app = Flask(__name__.split('.')[0])
    load_configs(app)
    initialize_logger(app)
    cache.init_app(app)
    cache.clear()
    db.init_app(app)

    if not standalone:
        with app.app_context():
            register_routes(app)
            _register_jobs(app)

    return app


def _register_jobs(app):
    from diablo.jobs.blackouts_job import BlackoutsJob  # noqa
    from diablo.jobs.clear_schedules_job import ClearSchedulesJob  # noqa
    from diablo.jobs.house_keeping_job import HouseKeepingJob  # noqa
    from diablo.jobs.kaltura_job import KalturaJob  # noqa
    from diablo.jobs.emails_job import EmailsJob  # noqa
    from diablo.jobs.remind_instructors_job import RemindInstructorsJob  # noqa
    from diablo.jobs.schedule_updates_job import ScheduleUpdatesJob  # noqa
    from diablo.jobs.semester_start_job import SemesterStartJob  # noqa
    from diablo.jobs.sis_data_refresh_job import SisDataRefreshJob  # noqa

    if app.config['JOBS_AUTO_START'] and (not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
        background_job_manager.start(app)
