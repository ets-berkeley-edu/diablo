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
from diablo.externals.kaltura import Kaltura
from diablo.merged.calnet import get_calnet_users_for_uids
from diablo.models.admin_user import AdminUser
from diablo.models.instructor import Instructor
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


def insert_or_update_instructors(instructor_uids):
    instructors = []
    for instructor in get_calnet_users_for_uids(app=app, uids=instructor_uids).values():
        instructors.append({
            'dept_code': instructor.get('deptCode'),
            'email': instructor.get('campusEmail') or instructor.get('email'),
            'first_name': instructor.get('firstName'),
            'last_name': instructor.get('lastName'),
            'uid': instructor['uid'],
        })

    Instructor.upsert(instructors)


def refresh_rooms():
    locations = SisSection.get_distinct_meeting_locations()
    existing_locations = Room.get_all_locations()
    new_locations = [location for location in locations if location not in existing_locations]
    if new_locations:
        app.logger.info(f'Creating {len(new_locations)} new rooms')
        for location in new_locations:
            Room.create(location=location)

    rooms = Room.all_rooms()
    kaltura_resource_ids_per_room = {}
    for resource in Kaltura().get_resource_list():
        room = next((r for r in rooms if r.location == resource['name']), None)
        if room:
            kaltura_resource_ids_per_room[room.id] = resource['id']

    if kaltura_resource_ids_per_room:
        Room.update_kaltura_resource_mappings(kaltura_resource_ids_per_room)


def get_courses_ready_to_schedule(approvals, term_id):
    ready_to_schedule = []

    scheduled_section_ids = [s.section_id for s in Scheduled.get_all_scheduled(term_id=term_id)]
    unscheduled_approvals = [approval for approval in approvals if approval.section_id not in scheduled_section_ids]

    if unscheduled_approvals:
        courses = SisSection.get_courses(section_ids=[a.section_id for a in unscheduled_approvals], term_id=term_id)
        courses_per_section_id = dict((int(course['sectionId']), course) for course in courses)
        admin_user_uids = set([user.uid for user in AdminUser.all_admin_users(include_deleted=True)])

        for section_id, uids in _get_uids_per_section_id(approvals=unscheduled_approvals).items():
            if admin_user_uids.intersection(set(uids)):
                ready_to_schedule.append(courses_per_section_id[section_id])
            else:
                course = courses_per_section_id[section_id]
                necessary_uids = [i['uid'] for i in course['instructors']]
                if all(uid in uids for uid in necessary_uids):
                    ready_to_schedule.append(courses_per_section_id[section_id])
    return ready_to_schedule


def _get_uids_per_section_id(approvals):
    uids_per_section_id = {approval.section_id: [] for approval in approvals}
    for approval in approvals:
        uids_per_section_id[approval.section_id].append(approval.approved_by_uid)
    return uids_per_section_id
