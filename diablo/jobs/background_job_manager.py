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
from datetime import datetime
import threading
import time

from diablo.jobs.base_job import BaseJob
from diablo.jobs.errors import BackgroundJobError
from diablo.models.job import Job
from diablo.models.job_history import JobHistory
import schedule


class BackgroundJobManager:

    def __init__(self):
        self.continuous_thread = None
        self.monitor = _Monitor()
        self.started_at = None

    def is_running(self):
        return self.monitor.is_running()

    def start(self, app):
        """Continuously run, executing pending jobs per time interval.

        It is intended behavior that ScheduleThread does not run missed jobs. For example, if you register a job that
        should run every minute and yet SCHEDULER_INTERVAL is set to one hour, then your job won't run 60 times at
        each interval. It will run once.
        """
        if self.is_running():
            return
        else:
            self.monitor.notify(is_running=True)
            self.started_at = datetime.now()

        class JobRunnerThread(threading.Thread):

            active = False

            @classmethod
            def run(cls):
                cls.active = True
                while self.monitor.is_running():
                    schedule.run_pending()
                    time.sleep(interval)
                schedule.clear()
                cls.active = False

        interval = app.config['JOBS_SECONDS_BETWEEN_PENDING_CHECK']
        job_configs = Job.get_all()
        app.logger.info(f"""

            Starting background job manager.
            Seconds between pending jobs check = {interval}
            Jobs:
                {[job_config.to_api_json() for job_config in job_configs]}

            """)

        # Clean up history for any older jobs that got lost.
        JobHistory.fail_orphans()

        if job_configs:
            for job_config in job_configs:
                job_key = job_config.key
                job_class = next(
                    (job for job in self.available_job_classes() if job.key() == job_key),
                    None,
                )
                if job_class:
                    job = job_class(app.app_context)
                else:
                    raise BackgroundJobError(f'Failed to find job with key {job_key}')

                type_ = job_config.job_schedule_type
                value = job_config.job_schedule_value
                if type_ == 'minutes':
                    schedule.every(int(value)).minutes.do(job.run)
                elif type_ == 'seconds':
                    schedule.every(int(value)).seconds.do(job.run)
                elif type_ == 'day_at':
                    schedule.every().day.at(value).do(job.run)
                else:
                    raise BackgroundJobError(f'Unrecognized schedule type: {type_}')

            self.continuous_thread = JobRunnerThread(daemon=True)
            self.continuous_thread.start()
        else:
            app.logger.warn('No jobs. Nothing scheduled.')

    def stop(self):
        """Cease the scheduler thread. Stops everything."""
        from flask import current_app as app

        app.logger.info('Stopping job-runner thread')
        self.monitor.notify(is_running=False)
        self.started_at = None

    def restart(self, app):
        if self.is_running():
            self.stop()
        self.start(app)

    def get_started_at(self):
        return self.started_at

    @classmethod
    def available_job_classes(cls):
        return BaseJob.__subclasses__()


class _Monitor:

    __is_running = None

    def __init__(self):
        if _Monitor.__is_running is not None:
            raise Exception('In singleton pattern, there can only be one instance.')

    @classmethod
    def notify(cls, is_running):
        if _Monitor.__is_running is None:
            _Monitor()
        _Monitor.__is_running = is_running

    @classmethod
    def is_running(cls):
        if _Monitor.__is_running is None:
            _Monitor()
        return _Monitor.__is_running is True
