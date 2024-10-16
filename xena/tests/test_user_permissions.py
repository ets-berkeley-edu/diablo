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

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait
from xena.models.meeting import Meeting
from xena.pages.course_page import CoursePage
from xena.pages.login_page import LoginPage
from xena.pages.ouija_board_page import OuijaBoardPage
from xena.test_utils import util


@pytest.mark.usefixtures('page_objects')
class TestUserPerms:

    test_data = util.get_test_script_course('test_user_permissions')
    section = util.get_test_section(test_data)
    meeting = section.meetings[0]
    instructor = section.instructors[0]

    def test_set_room_and_role(self):
        util.delete_term_instructor_rows(self.section.term, self.instructor)
        util.reset_test_data(self.section)

    def test_schedule_section(self):
        self.login_page.load_page()
        self.login_page.dev_auth()
        self.ouija_page.click_jobs_link()
        self.jobs_page.run_schedule_update_job_sequence()

    # NOTES

    def test_admin_cancel_course_note(self):
        util.delete_course_note(self.section)
        self.course_page.load_page(self.section)
        self.course_page.click_edit_note()
        self.course_page.click_cancel_note()
        assert self.course_page.note_text() == 'No notes.'

    def test_admin_edit_course_note(self):
        note = 'El Diablo (también ñuzco) es la personificación del mal tal como se concibe en diversas culturas'
        self.course_page.edit_note(note)
        assert self.course_page.note_text() == note

    def test_admin_delete_course_note(self):
        self.course_page.delete_note()
        assert self.course_page.note_text() == 'No notes.'

    def test_admin_edit_instructor_note(self):
        util.delete_instructor_note(self.instructor)
        note = "Satan (Hebraice הַשָּׂטָן, ha-Shatan, 'adversarius'), est nomen populare Diaboli"
        self.instructor_page.hit_admin_url(self.instructor)
        self.instructor_page.edit_note(note)
        assert self.instructor_page.note_text() == note

    def test_admin_delete_instructor_note(self):
        self.instructor_page.delete_note()
        assert self.instructor_page.note_text() == 'No notes.'

    # INSTRUCTOR RESTRICTIONS

    def test_instructor_login(self):
        self.jobs_page.log_out()
        self.login_page.load_page()
        self.login_page.dev_auth(self.instructor.uid)

    def test_no_instructor_notes(self):
        self.instructor_page.wait_for_title_containing(f'Your {self.section.term.name} Course')
        assert not self.instructor_page.is_present(self.instructor_page.NOTE_BODY)

    def test_no_course_notes(self):
        self.course_page.load_page(self.section)
        assert not self.course_page.is_present(self.course_page.NOTE_BODY)

    def test_no_ouija(self):
        self.ouija_page.hit_url()
        time.sleep(1)
        self.ouija_page.wait_for_diablo_title('Page not found')

    def test_no_rooms(self):
        self.rooms_page.hit_url()
        time.sleep(1)
        self.rooms_page.wait_for_diablo_title('Page not found')

    def test_no_instructor(self):
        self.instructor_page.hit_admin_url(self.instructor)
        time.sleep(1)
        self.instructor_page.wait_for_diablo_title('Page not found')

    def test_no_room(self):
        self.room_page.hit_url(self.meeting.room)
        time.sleep(1)
        self.room_page.wait_for_diablo_title('Page not found')

    def test_no_email_templates(self):
        self.templates_page.hit_url()
        time.sleep(1)
        self.templates_page.wait_for_diablo_title('Page not found')

    def test_no_jobs(self):
        self.jobs_page.hit_url()
        time.sleep(1)
        self.jobs_page.wait_for_diablo_title('Page not found')

    def test_no_attic(self):
        self.attic_page.hit_url()
        time.sleep(1)
        self.attic_page.wait_for_diablo_title('Page not found')

    def test_api_cache(self):
        self.api_page.hit_cache_clear()
        Wait(self.driver, util.get_short_timeout()).until(
            ec.presence_of_element_located((By.XPATH, '//*[contains(text(), "Unauthorized")]')),
        )

    def test_pi_role(self):
        self.course_page.load_page(self.section)
        assert self.course_page.is_present(CoursePage.COLLAB_EDIT_BUTTON)

    def test_icnt_role(self):
        util.set_instructor_role(self.section, self.instructor, 'ICNT')
        self.course_page.load_page(self.section)
        time.sleep(1)
        assert self.course_page.is_present(CoursePage.COLLAB_EDIT_BUTTON)

    def test_tnic_role(self):
        util.set_instructor_role(self.section, self.instructor, 'TNIC')
        self.course_page.load_page(self.section)
        time.sleep(1)
        assert self.course_page.is_present(CoursePage.COLLAB_EDIT_BUTTON)

    def test_aprx_role(self):
        self.course_page.log_out()
        util.set_instructor_role(self.section, self.instructor, 'APRX')
        self.login_page.dev_auth(self.instructor.uid)
        self.login_page.wait_for_element(LoginPage.ALERT_MSG, util.get_short_timeout())

    def test_invt_role(self):
        util.set_instructor_role(self.section, self.instructor, 'INVT')
        self.login_page.load_page()
        self.login_page.dev_auth(self.instructor.uid)
        self.login_page.wait_for_element(LoginPage.ALERT_MSG, util.get_short_timeout())

    def test_ineligible_room(self):
        meet = {'room': {'name': 'Chavez 3'}}
        meeting = Meeting(meet)
        util.set_meeting_location(self.section, meeting)
        util.set_instructor_role(self.section, self.instructor, 'PI')
        self.login_page.load_page()
        self.login_page.dev_auth(self.instructor.uid)
        self.ouija_page.wait_for_element(OuijaBoardPage.HOME_LINK, util.get_short_timeout())
        self.course_page.load_page(self.section)
        assert self.course_page.is_present(CoursePage.NOT_ELIGIBLE_MSG)

    def test_not_course_instructor(self):
        util.change_course_instructor(self.section, self.instructor)
        self.login_page.load_page()
        self.login_page.dev_auth(self.instructor.uid)
        self.login_page.wait_for_element(LoginPage.ALERT_MSG, util.get_short_timeout())

    def test_not_eligible_user(self):
        self.login_page.load_page()
        self.login_page.dev_auth('61889')
        self.login_page.wait_for_element(LoginPage.ALERT_MSG, util.get_short_timeout())
