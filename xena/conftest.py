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

import os

from diablo.factory import create_app
import pytest
from xena.models.term import Term
from xena.pages.api_page import ApiPage
from xena.pages.attic_page import AtticPage
from xena.pages.blackouts_page import BlackoutsPage
from xena.pages.calnet_page import CalNetPage
from xena.pages.canvas_page import CanvasPage
from xena.pages.course_changes_page import CourseChangesPage
from xena.pages.course_page import CoursePage
from xena.pages.courses_page import CoursesPage
from xena.pages.email_templates_page import EmailTemplatesPage
from xena.pages.instructor_page import InstructorPage
from xena.pages.jobs_page import JobsPage
from xena.pages.kaltura_page import KalturaPage
from xena.pages.login_page import LoginPage
from xena.pages.ouija_board_page import OuijaBoardPage
from xena.pages.room_page import RoomPage
from xena.pages.room_printable_page import RoomPrintablePage
from xena.pages.rooms_page import RoomsPage
from xena.test_utils.webdriver_manager import WebDriverManager


os.environ['DIABLO_ENV'] = 'xena'  # noqa

_app = create_app(standalone=True)

# Create app context before running tests.
ctx = _app.app_context()
ctx.push()


def pytest_addoption(parser):
    parser.addoption('--browser', action='store', default=_app.config['XENA_BROWSER'])
    parser.addoption('--headless', action='store')


@pytest.fixture(scope='session')
def page_objects(request):
    browser = request.config.getoption('--browser')
    headless = request.config.getoption('--headless')
    driver = WebDriverManager.launch_browser(browser=browser, headless=headless)

    term = Term()

    # Define page objects
    api_page = ApiPage(driver, headless)
    attic_page = AtticPage(driver, headless)
    blackouts_page = BlackoutsPage(driver, headless)
    calnet_page = CalNetPage(driver, headless)
    canvas_page = CanvasPage(driver, headless)
    changes_page = CourseChangesPage(driver, headless)
    courses_page = CoursesPage(driver, headless)
    instructor_page = InstructorPage(driver, headless)
    jobs_page = JobsPage(driver, headless)
    login_page = LoginPage(driver, headless)
    ouija_page = OuijaBoardPage(driver, headless)
    room_page = RoomPage(driver, headless)
    room_printable_page = RoomPrintablePage(driver, headless)
    rooms_page = RoomsPage(driver, headless)
    course_page = CoursePage(driver, headless)
    templates_page = EmailTemplatesPage(driver, headless)
    kaltura_page = KalturaPage(driver, headless)

    session = request.node
    try:
        for item in session.items:
            cls = item.getparent(pytest.Class)
            setattr(cls.obj, 'driver', driver)
            setattr(cls.obj, 'term', term)
            setattr(cls.obj, 'api_page', api_page)
            setattr(cls.obj, 'attic_page', attic_page)
            setattr(cls.obj, 'blackouts_page', blackouts_page)
            setattr(cls.obj, 'calnet_page', calnet_page)
            setattr(cls.obj, 'canvas_page', canvas_page)
            setattr(cls.obj, 'changes_page', changes_page)
            setattr(cls.obj, 'course_page', course_page)
            setattr(cls.obj, 'courses-page', courses_page)
            setattr(cls.obj, 'instructor_page', instructor_page)
            setattr(cls.obj, 'jobs_page', jobs_page)
            setattr(cls.obj, 'login_page', login_page)
            setattr(cls.obj, 'ouija_page', ouija_page)
            setattr(cls.obj, 'room_page', room_page)
            setattr(cls.obj, 'room_printable_page', room_printable_page)
            setattr(cls.obj, 'rooms_page', rooms_page)
            setattr(cls.obj, 'templates_page', templates_page)
            setattr(cls.obj, 'kaltura_page', kaltura_page)
        yield
    finally:
        WebDriverManager.quit_browser(driver)
