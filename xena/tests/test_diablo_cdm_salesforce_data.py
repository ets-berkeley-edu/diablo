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
import pytest
from xena.test_utils import util

test_data = util.parse_cdm_test_data()


@pytest.mark.usefixtures('cdm_salesforce_init')
@pytest.mark.parametrize('course', test_data, scope='class')
class TestCDMSalesforce:

    def test_project_search(self, course):
        if 'Salesforce' not in self.salesforce_page.title():
            self.salesforce_page.log_in()
        else:
            app.logger.info('Found Salesforce in the page title')
        self.salesforce_page.search_for_project(course['ccn'])
        self.salesforce_page.click_project_result_link(course['courseName'])

    def test_project_name(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.course_name_xpath(course['courseName'])) is True

    def test_course_offering_id(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.course_id_xpath(course['courseOfferingId'])) is True

    def test_parent_project(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.parent_project_xpath('Spring 2020 Course Captures')) is True

    def test_project_end_date(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.project_end_date_xpath('6/12/2020')) is True

    def test_num_instructors(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.num_instructors_xpath(f'{len(course["instructors"])}')) is True

    # TODO test_instructors

    def test_schedule_days(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.schedule_days_xpath(course['scheduleDays'])) is True

    def test_start_time(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.start_time_xpath(course['startTime'])) is True

    def test_end_time(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.end_time_xpath(course['endTime'])) is True

    # TODO test_room

    def test_sign_up_link(self, course):
        href = f'http://webcast-cc.ets.berkeley.edu/signUp.html?id=2020B{course["ccn"]}'
        assert self.salesforce_page.data_el_exists(self.salesforce_page.sign_up_link_xpath(href)) is True

    def test_ccn(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.ccn_xpath(course['ccn'])) is True

    def test_course_title(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.course_title_xpath(course['courseName'])) is True

    def test_section_number(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.section_xpath(course['section'])) is True

    def test_semester(self, course):
        assert self.salesforce_page.data_el_exists(self.salesforce_page.semester_xpath(course['semester'])) is True
