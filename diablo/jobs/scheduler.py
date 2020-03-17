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

import schedule


class Scheduler:

    def __init__(self):
        self.cease_continuous_run = threading.Event()
        self.continuous_thread = None

    def start(self, app):
        """Continuously run, executing pending jobs per time interval.

        It is intended behavior that ScheduleThread does not run missed jobs. For example, if you register a job that
        should run every minute and yet SCHEDULER_INTERVAL is set to one hour, then your job won't run 60 times at
        each interval. It will run once.
        """
        scheduler_config = app.config['SCHEDULER']
        interval = scheduler_config['interval_seconds']
        jobs = scheduler_config['jobs']

        if jobs:
            for job in jobs:
                callable_ = job['callable']
                type_ = job['schedule']['type']
                value = job['schedule']['value']

                if type_ == 'minutes':
                    schedule.every(value).minutes.do(callable_)
                elif type_ == 'seconds':
                    schedule.every(value).seconds.do(callable_)
                elif type_ == 'day_at':
                    schedule.every().day.at(value).do(callable_)
                else:
                    raise BackgroundJobError(f'Unrecognized schedule type: {type_}')

            class ScheduleThread(threading.Thread):
                @classmethod
                def run(cls):
                    while not self.cease_continuous_run.is_set():
                        schedule.run_pending()
                        time.sleep(interval)
                    schedule.clear()

            self.continuous_thread = ScheduleThread()
            self.continuous_thread.start()

        else:
            app.logger.warn('No jobs registered. Scheduler will do nothing.')

    def stop(self):
        """Cease the scheduler thread. Stops everything."""
        self.cease_continuous_run.set()


class BackgroundJobError(Exception):
    pass
