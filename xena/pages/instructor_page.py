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

from flask import current_app as app
from selenium.webdriver.common.by import By
from xena.pages.courses_page import CoursesPage


class InstructorPage(CoursesPage):

    def hit_admin_url(self, instructor):
        self.driver.get(f'{app.config["BASE_URL"]}/user/{instructor.uid}')

    OPT_OUT_ALL_BUTTON = By.ID, 'toggle-opt-out-all-terms'
    OPT_OUT_CURRENT_BUTTON = By.ID, 'toggle-opt-out-current-term'

    @staticmethod
    def opt_out_section_button_loc(section):
        return By.ID, f'toggle-opt-out-{section.ccn}'

    def enable_opt_out_all_terms(self):
        app.logger.info('Opting out of all terms')
        if self.element(self.OPT_OUT_ALL_BUTTON).get_attribute('aria-checked') == 'false':
            self.wait_for_element_and_click(self.OPT_OUT_ALL_BUTTON)
        else:
            app.logger.info('Already opted out of all terms')

    def disable_opt_out_all_terms(self):
        app.logger.info('Unchecking opt-out-all-terms')
        if self.element(self.OPT_OUT_ALL_BUTTON).get_attribute('aria-checked') == 'true':
            self.wait_for_element_and_click(self.OPT_OUT_ALL_BUTTON)
        else:
            app.logger.info('Already disabled')

    def enable_opt_out_current_term(self):
        app.logger.info('Opting out of current term')
        if self.element(self.OPT_OUT_CURRENT_BUTTON).get_attribute('aria-checked') == 'false':
            self.wait_for_element_and_click(self.OPT_OUT_CURRENT_BUTTON)
        else:
            app.logger.info('Already opted out of current term')

    def disable_opt_out_current_term(self):
        app.logger.info('Unchecking opt-out-current-term')
        if self.element(self.OPT_OUT_CURRENT_BUTTON).get_attribute('aria-checked') == 'true':
            self.wait_for_element_and_click(self.OPT_OUT_CURRENT_BUTTON)
        else:
            app.logger.info('Already disabled')

    def enable_opt_out_section(self, section):
        app.logger.info(f'Opting out of section ID {section.ccn}')
        if self.element(self.opt_out_section_button_loc(section)).get_attribute('aria-checked') == 'false':
            self.wait_for_element_and_click(self.opt_out_section_button_loc(section))
        else:
            app.logger.info(f'Already opted out of section {section.ccn}')

    def disable_opt_out_section(self, section):
        app.logger.info(f'Unchecking opt-out-{section.ccn}')
        if self.element(self.opt_out_section_button_loc(section)).get_attribute('aria-checked') == 'true':
            self.wait_for_element_and_click(self.opt_out_section_button_loc(section))
        else:
            app.logger.info('Already disabled')
