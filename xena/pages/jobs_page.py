"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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
    RUN_BLACKOUTS_JOB_BUTTON = (By.ID, 'run-job-blackouts')
    RUN_KALTURA_JOB_BUTTON = (By.ID, 'run-job-kaltura')
    RUN_EMAILS_JOB_BUTTON = (By.ID, 'run-job-emails')
    RUN_REMIND_OPT_OUTS_BUTTON = (By.ID, 'run-job-remind_opt_outs')
    RUN_REMIND_PARTIALLY_APPROVED_BUTTON = (By.ID< 'run-job-remind_partially_approved')
    RUN_REMIND_SCHEDULED_BUTTON = (By.ID, 'run-job-remind_scheduled')
    RUN_SCHEDULE_UPDATES_JOB_BUTTON = (By.ID, 'run-job-schedule_updates')
    RUN_SEMESTER_START_JOB_BUTTON = (By.ID, 'run-job-semester_start')

    SEARCH_HISTORY_INPUT = (By.ID, 'search-job-history-input')

    def hit_url(self):
        self.driver.get(f'{app.config["BASE_URL"]}/jobs')

    def load_page(self):
        if 'The Chancel' not in self.title():
            app.logger.info("Loading the 'Chancel' page")
            self.hit_url()
            self.wait_for_diablo_title('The Chancel')

    def run_blackouts_job(self):
        app.logger.info('Running the Blackouts job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_BLACKOUTS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.BLACKOUTS)

    def run_kaltura_job(self):
        app.logger.info('Running Kaltura job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_KALTURA_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.KALTURA)

    def run_emails_job(self):
        app.logger.info('Running queued emails job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_EMAILS_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.EMAILS)

    def run_remind_scheduled_job(self):
        app.logger.info('Running remind scheduled job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_REMIND_SCHEDULED_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.REMIND_SCHEDULED)

    def run_remind_opt_outs_job(self):
        app.logger.info('Running remind opt-outs job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_REMIND_OPT_OUTS_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.REMIND_OPT_OUTS)

    def run_remind_partially_approved_job(self):
        app.logger.info('Running remind partially approved job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_REMIND_PARTIALLY_APPROVED_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.REMIND_PARTIALLY_APPROVED)

    def run_schedule_updates_job(self):
        app.logger.info('Running Schedule Updates job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_SCHEDULE_UPDATES_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.SCHEDULE_UPDATES)

    def run_semester_start_job(self):
        app.logger.info('Running Semester Start job')
        self.scroll_to_top()
        time.sleep(1)
        self.wait_for_page_and_click(JobsPage.RUN_SEMESTER_START_JOB_BUTTON)
        self.wait_for_most_recent_job_success(AsyncJob.SEMESTER_START)

    def run_remind_opt_outs_job_sequence(self):
        self.load_page()
        self.run_remind_opt_outs_job()
        self.run_emails_job()

    def run_remind_partially_approved_job_sequence(self):
        self.load_page()
        self.run_remind_partially_approved_job()
        self.run_emails_job()

    def run_remind_scheduled_job_sequence(self):
        self.load_page()
        self.run_remind_scheduled_job()
        self.run_emails_job()

    def run_semester_start_job_sequence(self):
        self.run_semester_start_job()
        self.run_emails_job()

    def run_schedule_update_job_sequence(self):
        self.load_page()
        self.run_schedule_updates_job()
        self.run_emails_job()

    def run_schedule_update_and_kaltura_job_sequence(self):
        self.load_page()
        self.run_schedule_updates_job()
        self.run_kaltura_job()
        self.run_emails_job()

    def run_settings_update_job_sequence(self):
        self.load_page()
        self.run_kaltura_job()
        self.run_emails_job()

    def wait_for_jobs_table(self):
        locator = By.XPATH, '//div[@id="job-schedule-table"]//table'
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
        self.click_jobs_link()
        for job in AsyncJob:
            app.logger.info(f'Not disabling {job}')

    def search_job_history(self, async_job):
        app.logger.info(f'Searching for {async_job.value}')
        self.wait_for_element_and_type(JobsPage.SEARCH_HISTORY_INPUT, async_job.value)

    @staticmethod
    def job_most_recent_xpath(async_job):
        return f'//div[@id="job-history-table"]//tbody/tr[contains(., "{async_job.value}")][1]'

    def wait_for_most_recent_job_success(self, async_job):
        app.logger.info(f'Waiting for {async_job} to succeed')
        time.sleep(2)
        tries = 0
        retries = util.get_short_timeout()
        success = By.XPATH, f'{JobsPage.job_most_recent_xpath(async_job)}//i[contains(@title, "job finished")]'
        failure = By.XPATH, f'{JobsPage.job_most_recent_xpath(async_job)}//i[contains(@title, "job failed")]'
        while tries <= retries:
            tries += 1
            try:
                app.logger.info('Waiting for success')
                self.when_present(success, util.get_short_timeout())
                app.logger.info('Job succeeded')
                break
            except TimeoutException:
                if self.is_present(failure):
                    app.logger.info('Job failed')
                    raise
                elif tries == retries:
                    app.logger.info('Timed out')
                    raise
                else:
                    app.logger.info('Retrying')
