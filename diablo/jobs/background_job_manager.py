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
import threading
import time

from diablo.jobs.errors import BackgroundJobError
import schedule


class BackgroundJobManager:

    def __init__(self, available_job_classes):
        self.cease_continuous_run = threading.Event()
        self.continuous_thread = None
        self._job_classes = available_job_classes

    def start(self, app):
        """Continuously run, executing pending jobs per time interval.

        It is intended behavior that ScheduleThread does not run missed jobs. For example, if you register a job that
        should run every minute and yet SCHEDULER_INTERVAL is set to one hour, then your job won't run 60 times at
        each interval. It will run once.
        """
        class JobRunnerThread(threading.Thread):

            active = False

            @classmethod
            def run(cls):
                cls.active = True
                while not self.cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)
                schedule.clear()
                cls.active = False

        if JobRunnerThread.active:
            return

        scheduler_config = app.config['JOB_MANAGER']
        interval = scheduler_config['seconds_between_pending_jobs_check']
        job_configs = scheduler_config['jobs']
        app.logger.info(f"""

            Starting background job manager.
            Seconds between pending jobs check = {interval}
            Jobs:
                {job_configs}

            """)
        if job_configs:
            for job_config in job_configs:
                self._add_job_to_schedule(app=app, job_config=job_config)

            self.continuous_thread = JobRunnerThread(daemon=True)
            self.continuous_thread.start()
        else:
            app.logger.warn('No jobs. Nothing scheduled.')

    def stop(self):
        """Cease the scheduler thread. Stops everything."""
        from flask import current_app as app

        app.logger.info('Stopping job-runner thread')
        self.cease_continuous_run.set()

    def _add_job_to_schedule(self, app, job_config):
        if job_config.get('disabled', False) is True:
            return

        job_key = job_config['key']
        job_class = next((job for job in self._job_classes if job.key() == job_key), None)

        if job_class:
            job = job_class(app.app_context)
        else:
            raise BackgroundJobError(f'Failed to find job with key {job_key}')

        type_ = job_config['schedule']['type']
        value = job_config['schedule']['value']

        run_with_context = job.run_with_app_context
        if type_ == 'minutes':
            schedule.every(value).minutes.do(run_with_context)
        elif type_ == 'seconds':
            schedule.every(value).seconds.do(run_with_context)
        elif type_ == 'day_at':
            schedule.every().day.at(value).do(run_with_context)
        else:
            raise BackgroundJobError(f'Unrecognized schedule type: {type_}')
