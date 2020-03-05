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

import pytest
from xena.pages.google_page import GooglePage
from xena.test_utils.webdriver_manager import WebDriverManager


@pytest.fixture(scope='class')
def driver_init(request):
    driver = WebDriverManager.launch_browser()
    google_page = GooglePage(driver)
    request.cls.google_page = google_page
    yield
    WebDriverManager.quit_browser(driver)


@pytest.mark.usefixtures('driver_init')
class TestTests:

    def test_xena(self):
        self.google_page.load_page()
        self.google_page.enter_search_string('Xena')
        self.google_page.hit_enter()
        self.google_page.wait_for_title('Xena - Google Search')

    def test_gabrielle(self):
        self.google_page.enter_search_string('Gabrielle')
        self.google_page.hit_enter()
        self.google_page.wait_for_title('Gabrielle - Google Search')
