"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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

from flask import current_app as app
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.models.async_job import AsyncJob
from xena.pages.diablo_pages import DiabloPages
from xena.test_utils import util


class JobsPage(DiabloPages):
    RUN_ADMIN_EMAILS_JOB_BUTTON = (By.ID, 'run-job-admin_emails')
    RUN_BLACKOUTS_JOB_BUTTON = (By.ID, 'run-job-blackouts')
    RUN_CANVAS_JOB_BUTTON = (By.ID, 'run-job-canvas')
    RUN_HOUSEKEEPING_JOB_BUTTON = (By.ID, 'run-job-house_keeping')
    RUN_INSTRUCTOR_EMAILS_JOB_BUTTON = (By.ID, 'run-job-instructor_emails')
    RUN_INVITATIONS_JOB = (By.ID, 'run-job-invitations')
    RUN_KALTURA_JOB_BUTTON = (By.ID, 'run-job-kaltura')
    RUN_QUEUED_EMAILS_JOB_BUTTON = (By.ID, 'run-job-queued_emails')
    RUN_SIS_DATA_REFRESH_JOB_BUTTON = (By.ID, 'run-job-sis_data_refresh')

    SEARCH_HISTORY_INPUT = (By.XPATH, '//label[text()="Search History"]/following-sibling::input')

    def hit_url(self):
        self.driver.get(f'{app.config["BASE_URL"]}/jobs')

    def load_page(self):
        app.logger.info("Loading the 'Engine Room' page")
        self.hit_url()
        self.wait_for_diablo_title('The Engine Room')

    def run_admin_emails_job(self):
        app.logger.info('Running the admin emails job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_ADMIN_EMAILS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.ADMIN_EMAILS)

    def run_blackouts_job(self):
        app.logger.info('Running the Blackouts job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_BLACKOUTS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.BLACKOUTS)

    def run_canvas_job(self):
        app.logger.info('Running the Canvas job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_CANVAS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.CANVAS)

    def run_housekeeping_job(self):
        app.logger.info('Vacuuming, dusting, and scrubbing the tub')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_HOUSEKEEPING_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.HOUSEKEEPING)

    def run_instructor_emails_job(self):
        app.logger.info('Running instructor emails job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_INSTRUCTOR_EMAILS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.INSTRUCTOR_EMAILS)

    def run_invitations_job(self):
        app.logger.info('Running invitations job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_INVITATIONS_JOB)
        self.wait_for_most_recent_job_success(AsyncJob.INVITATIONS)

    def run_kaltura_job(self):
        app.logger.info('Running Kaltura job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_KALTURA_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.KALTURA)

    def run_queued_emails_job(self):
        app.logger.info('Running queued emails job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_QUEUED_EMAILS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.QUEUED_EMAILS)

    def run_sis_data_refresh_job(self):
        app.logger.info('Running SIS data refresh job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_SIS_DATA_REFRESH_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.SIS_DATA_REFRESH)

    def wait_for_jobs_table(self):
        locator = By.XPATH, '//h1[contains(., "The Engine Room")]/../../following-sibling::div//table'
        Wait(self.driver, util.get_short_timeout()).until(ec.presence_of_element_located(locator))

    @staticmethod
    def job_toggle_id(async_job):
        return f'job-{async_job.value}-enabled'

    @staticmethod
    def enabled_job_locator(async_job):
        el_id = JobsPage.job_toggle_id(async_job)
        xpath = f'//input[@id="{el_id}"][contains(@aria-label, "is enabled")]/following-sibling::div'
        return By.XPATH, xpath

    @staticmethod
    def disabled_job_locator(async_job):
        el_id = JobsPage.job_toggle_id(async_job)
        xpath = f'//input[@id="{el_id}"][contains(@aria-label, "is disabled")]/following-sibling::div'
        return By.XPATH, xpath

    def disable_job(self, async_job):
        app.logger.info(f'Making sure {async_job.value} is disabled')
        self.wait_for_jobs_table()
        if self.is_present(JobsPage.enabled_job_locator(async_job)):
            app.logger.info('Disabling job')
            self.click_element_js(JobsPage.enabled_job_locator(async_job))
            Wait(self.driver, 2).until(ec.presence_of_element_located(JobsPage.disabled_job_locator(async_job)))
        else:
            app.logger.info('Job is already disabled')

    def enable_job(self, async_job):
        app.logger.info(f'Making sure {async_job.value} is enabled')
        self.wait_for_jobs_table()
        if self.is_present(JobsPage.disabled_job_locator(async_job)):
            app.logger.info('Enabling job')
            self.element(JobsPage.disabled_job_locator(async_job)).click()
            Wait(self.driver, 2).until(ec.presence_of_element_located(JobsPage.enabled_job_locator(async_job)))
        else:
            app.logger.info('Job is already enabled')

    def disable_all_jobs(self):
        for job in AsyncJob:
            self.disable_job(job)

    def search_job_history(self, async_job):
        app.loggerinfo(f'Searching for {async_job.value}')
        self.wait_for_element_and_type(async_job.value)

    @staticmethod
    def job_row_one_locator():
        return '//h2[contains(text(), "History")]/../../following-sibling::div//tbody/tr[1]'

    @staticmethod
    def job_most_recent_locator(async_job):
        xpath = f'{JobsPage.job_row_one_locator()}[contains(., "{async_job.value}")]'
        return By.XPATH, xpath

    def wait_for_most_recent_job_success(self, async_job):
        app.logger.info(f'Waiting for {async_job} to succeed')
        time.sleep(2)
        tries = 1
        retries = util.get_long_timeout()
        success = By.XPATH, f'{JobsPage.job_most_recent_locator(async_job)[1]}//i[contains(@class, "light-green--text")]'
        failure = By.XPATH, f'{JobsPage.job_most_recent_locator(async_job)[1]}//i[contains(@class, "red--text")]'
        while tries <= retries:
            tries += 1
            try:
                if self.is_present(success):
                    app.logger.info('Job succeeded')
                    break
                else:
                    if self.is_present(JobsPage.ERROR_REDIRECT):
                        self.load_page()
                    Wait(self.driver, 1).until(ec.visibility_of_element_located(failure))
                    app.logger.info('Job failed')
                    break
            except TimeoutException:
                if tries == retries:
                    raise
                else:
                    time.sleep(1)
        Wait(self.driver, 1).until(ec.visibility_of_element_located(success))
