"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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
from xena.models.capability import Capability
from xena.models.recording_type import RecordingType
from xena.test_utils import util


room_data = util.parse_rooms_data()


@pytest.mark.usefixtures('page_objects')
@pytest.mark.parametrize('room', room_data, scope='class', ids=[room.name for room in room_data])
class TestEnableRooms:

    screencast_rooms = [classroom for classroom in room_data if classroom.capability == Capability.SCREENCAST]
    video_rooms = [classroom for classroom in room_data if classroom.capability == Capability.SCREENCAST_AND_VIDEO]

    def test_room_search(self, room):
        if 'Course Capture' not in self.rooms_page.title():
            self.login_page.load_page()
            self.login_page.dev_auth(util.get_admin_uid())
            self.ouija_page.click_rooms_link()
        else:
            app.logger.info('Already logged in')
            self.rooms_page.load_page()
        self.rooms_page.wait_for_rooms_list()
        self.rooms_page.find_room(room)

    def test_room_link(self, room):
        self.rooms_page.click_room_link(room)
        self.room_page.wait_for_diablo_title(room.name)

    def test_set_capability(self, room):
        self.room_page.set_capability(room.capability)

    def test_screencast_and_auditorium_true(self, room):
        if room == self.screencast_rooms[0]:
            self.room_page.set_auditorium_true()
            self.room_page.click_first_course_link()
            self.sign_up_page.click_rec_type_input()
            visible_opts = self.sign_up_page.visible_menu_options()
            expected = [RecordingType.SCREENCAST.value['option']]
            assert visible_opts == expected

    def test_screencast_and_auditorium_false(self, room):
        if room == self.screencast_rooms[0]:
            self.sign_up_page.click_room_link(room)
            self.room_page.set_auditorium_false()
            self.room_page.click_first_course_link()
            self.sign_up_page.click_rec_type_input()
            visible_opts = self.sign_up_page.visible_menu_options()
            expected = [RecordingType.SCREENCAST.value['option']]
            assert visible_opts == expected

    def test_video_and_auditorium_false(self, room):
        if room == self.video_rooms[0]:
            self.room_page.set_auditorium_false()
            self.room_page.click_first_course_link()
            self.sign_up_page.click_rec_type_input()
            visible_opts = self.sign_up_page.visible_menu_options()
            expected = [RecordingType.SCREENCAST_AND_VIDEO.value['option']]
            assert visible_opts == expected

    def test_video_and_auditorium_true(self, room):
        if room == self.video_rooms[0]:
            self.sign_up_page.click_room_link(room)
            self.room_page.set_auditorium_true()
            self.room_page.click_first_course_link()
            self.sign_up_page.click_rec_type_input()
            visible_opts = self.sign_up_page.visible_menu_options()
            expected = [
                RecordingType.SCREENCAST.value['option'], RecordingType.VIDEO.value['option'],
                RecordingType.SCREENCAST_AND_VIDEO.value['option'],
            ]
            assert visible_opts == expected
