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
from datetime import datetime
import os
import threading
import time

from diablo.externals import rds
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
        should run every minute and yet JOBS_SECONDS_BETWEEN_PENDING_CHECK is set to one hour, then your job won't run
        60 times at each interval. It will run once.
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
        all_jobs = Job.get_all()
        app.logger.info(f"""

            Starting background job manager.
            Seconds between pending jobs check = {interval}
            Jobs:
                {[job.to_api_json() for job in all_jobs]}

            """)

        # If running on EC2, tell the database that this instance is the one now running scheduled jobs.
        instance_id = os.environ.get('EC2_INSTANCE_ID')
        if instance_id:
            rds.execute(
                'DELETE FROM job_runner; INSERT INTO job_runner (ec2_instance_id) VALUES (%s);',
                params=(instance_id,),
            )

        # Clean up history for any older jobs that got lost.
        JobHistory.fail_orphans()

        if all_jobs:
            for job_config in all_jobs:
                self._load_job(
                    app=app,
                    job_key=job_config.key,
                    schedule_type=job_config.job_schedule_type,
                    schedule_value=job_config.job_schedule_value,
                )

            self.continuous_thread = JobRunnerThread(daemon=True)
            self.continuous_thread.start()
        else:
            app.logger.warn('No jobs. Nothing scheduled.')

    def restart(self):
        from flask import current_app as app

        self.monitor.notify(is_running=False)
        self.started_at = None
        schedule.clear()

        self.start(app=app)
        app.logger.info('Job manager restarted')

    def get_started_at(self):
        return self.started_at

    @classmethod
    def available_job_classes(cls):
        return BaseJob.__subclasses__()

    def _load_job(self, app, job_key, schedule_type, schedule_value):
        job_class = next((job for job in self.available_job_classes() if job.key() == job_key), None)
        if job_class:
            task_runner = job_class(app.app_context)
        else:
            raise BackgroundJobError(f'Failed to find job with key {job_key}')

        if schedule_type == 'minutes':
            schedule.every(int(schedule_value)).minutes.do(task_runner.run)
        elif schedule_type == 'seconds':
            schedule.every(int(schedule_value)).seconds.do(task_runner.run)
        elif schedule_type == 'day_at':
            schedule.every().day.at(schedule_value).do(task_runner.run)
        else:
            raise BackgroundJobError(f'Unrecognized schedule type: {schedule_type}')


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
