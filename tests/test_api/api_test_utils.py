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
import random

from diablo import cachify, std_commit
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection


def api_get_course(client, term_id, section_id, expected_status_code=200):
    response = client.get(f'/api/course/{term_id}/{section_id}')
    assert response.status_code == expected_status_code, f"""
        Expected status code: {expected_status_code}
        Actual status code: {response.status_code}
        section_id: {section_id}
    """
    return response.json


def api_get_user(client, uid, expected_status_code=200):
    response = client.get(f'/api/user/{uid}')
    assert response.status_code == expected_status_code, f"""
        Expected status code: {expected_status_code}
        Actual status code: {response.status_code}
        uid: {uid}
    """
    return response.json


def get_eligible_meeting(section_id, term_id):
    feed = SisSection.get_course(term_id=term_id, section_id=section_id, include_deleted=True)
    return (feed['meetings']['eligible'] + feed['meetings']['ineligible'])[0]


@cachify('instructor_uids_{section_id}_{term_id}')
def get_instructor_uids(section_id, term_id):
    course = SisSection.get_course(section_id=section_id, term_id=term_id, include_deleted=True)
    return [instructor['uid'] for instructor in course['instructors']]


def mock_scheduled(
        section_id,
        term_id,
        meeting=None,
        override_days=None,
        override_end_date=None,
        override_end_time=None,
        override_room_id=None,
        override_start_date=None,
        override_start_time=None,
        publish_type='kaltura_media_gallery',
        recording_type='presenter_presentation_audio',
):
    meeting = meeting or get_eligible_meeting(section_id=section_id, term_id=term_id)
    Scheduled.create(
        course_display_name=f'term_id:{term_id} section_id:{section_id}',
        instructor_uids=get_instructor_uids(term_id=term_id, section_id=section_id),
        collaborator_uids=[],
        kaltura_schedule_id=random.randint(1, 10),
        meeting_days=override_days or meeting['days'],
        meeting_end_date=override_end_date or get_recording_end_date(meeting),
        meeting_end_time=override_end_time or meeting['endTime'],
        meeting_start_date=override_start_date or get_recording_start_date(meeting, return_today_if_past_start=True),
        meeting_start_time=override_start_time or meeting['startTime'],
        publish_type_=publish_type,
        recording_type_=recording_type,
        room_id=override_room_id or Room.get_room_id(section_id=section_id, term_id=term_id),
        section_id=section_id,
        term_id=term_id,
    )
    std_commit(allow_test_environment=True)
