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

import os

from diablo.factory import create_app
import pytest
from xena.models.recording_schedule import RecordingSchedule
from xena.models.section import Section
from xena.pages.login_page import LoginPage
from xena.pages.ouija_board_page import OuijaBoardPage
from xena.pages.sign_up_page import SignUpPage
from xena.test_utils import util
from xena.test_utils.webdriver_manager import WebDriverManager


os.environ['DIABLO_ENV'] = 'xena'  # noqa

_app = create_app()

# Create app context before running tests.
ctx = _app.app_context()
ctx.push()


@pytest.fixture(scope='session')
def sign_up_0_test(request):
    driver = WebDriverManager.launch_browser()

    # Reset course data in Diablo and Kaltura
    test_data = util.parse_sign_up_test_data()
    util.reset_test_data(test_data[0])

    # Define the course data for the test
    section = Section(test_data[0])
    recording_schedule = RecordingSchedule(section)

    # Define page objects
    login_page = LoginPage(driver)
    ouija_page = OuijaBoardPage(driver)
    sign_up_page = SignUpPage(driver)

    session = request.node
    try:
        for item in session.items:
            cls = item.getparent(pytest.Class)
            setattr(cls.obj, 'section', section)
            setattr(cls.obj, 'recording_schedule', recording_schedule)
            setattr(cls.obj, 'driver', driver)
            setattr(cls.obj, 'login_page', login_page)
            setattr(cls.obj, 'ouija_page', ouija_page)
            setattr(cls.obj, 'sign_up_page', sign_up_page)
        yield
    finally:
        WebDriverManager.quit_browser(driver)
