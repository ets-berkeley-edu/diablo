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
import traceback

from diablo.jobs.errors import BackgroundJobError
from diablo.merged.emailer import send_system_error_email
from diablo.models.job_history import JobHistory
from flask import current_app as app


class BaseJob:

    def __init__(self, app_context):
        self.app_context = app_context

    def run_with_app_context(self):
        with self.app_context():
            if JobHistory.is_job_running(job_key=self.key()):
                app.logger.warn(f'Skipping job {self.key()} because an older instance is still running')

            else:
                app.logger.info(f'Job {self.key()} is starting.')
                job_tracker = JobHistory.job_started(job_key=self.key())
                try:
                    self.run()
                    JobHistory.job_finished(id_=job_tracker.id)
                    app.logger.info(f'Job {self.key()} finished successfully.')

                except Exception as e:
                    trace = traceback.format_exc()
                    summary = f'Job {self.key()} failed'
                    app.logger.error(summary)
                    app.logger.exception(e)
                    send_system_error_email(
                        message=f'{summary}. Detailed error information appears below.\n\n{trace}',
                        subject=summary,
                    )
                    JobHistory.job_finished(id_=job_tracker.id, failed=True)

    def run(self):
        raise BackgroundJobError('Implement this method in Job sub-class')

    @classmethod
    def key(cls):
        raise BackgroundJobError('Implement this method in Job sub-class')

    @classmethod
    def description(cls):
        raise BackgroundJobError('Implement this method in Job sub-class')
