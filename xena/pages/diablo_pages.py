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
from xena.pages.page import Page


class DiabloPages(Page):

    OUIJA_BOARD_LINK = (By.ID, 'sidebar-link-Ouija Board')
    ROOMS_LINK = (By.ID, 'sidebar-link-Rooms')
    COURSE_CHANGES_LINK = (By.ID, 'sidebar-link-Course Changes')

    MENU_BUTTON = (By.ID, 'btn-main-menu')
    EMAIL_TEMPLATES_LINK = (By.ID, 'menu-item-email-templates')
    JOBS_LINK = (By.ID, 'menu-item-jobs')
    JOB_HISTORY_LINK = (By.ID, 'menu-item-job-history')
    LOG_OUT_LINK = (By.ID, 'menu-item-log-out')

    def wait_for_diablo_title(self, string):
        self.wait_for_title(f'{string} | Course Capture')

    def click_ouija_board_link(self):
        app.logger.info('Clicking Ouija Board link')
        self.wait_for_element_and_click(DiabloPages.OUIJA_BOARD_LINK)

    def click_rooms_link(self):
        app.logger.info('Clicking Rooms link')
        self.wait_for_element_and_click(DiabloPages.ROOMS_LINK)

    def click_course_changes_link(self):
        app.logger.info('Clicking Course Changes link')
        self.wait_for_element_and_click(DiabloPages.COURSE_CHANGES_LINK)

    def click_menu_button(self):
        self.wait_for_element_and_click(DiabloPages.MENU_BUTTON)

    def open_menu(self):
        if not self.element(DiabloPages.LOG_OUT_LINK).is_displayed():
            self.click_menu_button()

    def click_email_templates_link(self):
        app.logger.info('Clicking Email Templates link')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.EMAIL_TEMPLATES_LINK)

    def click_jobs_link(self):
        app.logger.info('Clicking Jobs link')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.JOBS_LINK)

    def click_job_history_link(self):
        app.logger.info('Clicking Job History link')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.JOB_HISTORY_LINK)

    def log_out(self):
        app.logger.info('Logging out')
        self.open_menu()
        self.wait_for_element_and_click(DiabloPages.LOG_OUT_LINK)
