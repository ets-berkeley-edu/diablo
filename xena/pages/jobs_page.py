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

from flask import current_app as app
from selenium.webdriver.common.by import By
from xena.pages.diablo_pages import DiabloPages


class JobsPage(DiabloPages):

    RUN_ADMIN_EMAILS_JOB_BUTTON = (By.ID, 'run-job-admin_emails_job')
    RUN_CANVAS_JOB_BUTTON = (By.ID, 'run-job-canvas_job')
    RUN_DBLINK_TO_REDSHIFT_JOB_BUTTON = (By.ID, 'run-job-dblink_to_redshift_job')
    RUN_KALTURA_JOB_BUTTON = (By.ID, 'run-job-kaltura_job')
    RUN_QUEUED_EMAILS_JOB_BUTTON = (By.ID, 'run-job-queued_emails_job')

    def run_admin_emails_job(self):
        app.logger.info('Running the admin emails job')
        self.wait_for_element_and_click(JobsPage.RUN_ADMIN_EMAILS_JOB_BUTTON)

    def run_canvas_job(self):
        app.logger.info('Running the Canvas job')
        self.wait_for_element_and_click(JobsPage.RUN_CANVAS_JOB_BUTTON)

    def run_dblink_to_redshift_job(self):
        app.logger.info('Running DBLink to Redshift job')
        self.wait_for_element_and_click(JobsPage.RUN_DBLINK_TO_REDSHIFT_JOB_BUTTON)

    def run_kaltura_job(self):
        app.logger.info('Running Kaltura job')
        self.wait_for_element_and_click(JobsPage.RUN_KALTURA_JOB_BUTTON)

    def run_queued_emails_job(self):
        app.logger.info('Running queued emails job')
        self.wait_for_element_and_click(JobsPage.RUN_QUEUED_EMAILS_JOB_BUTTON)
