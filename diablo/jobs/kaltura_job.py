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
from datetime import date, datetime, time, timedelta

from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.lib.util import format_days, objects_to_dict_organized_by_section_id
from diablo.merged.emailer import notify_instructors_recordings_scheduled
from diablo.models.admin_user import AdminUser
from diablo.models.approval import Approval
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class KalturaJob(BaseJob):

    def run(self, args=None):
        term_id = app.config['CURRENT_TERM_ID']
        approvals = Approval.get_approvals_per_term(term_id=term_id)
        if approvals:
            approvals_per_section_id = objects_to_dict_organized_by_section_id(objects=approvals)
            ready_to_schedule = _get_courses_ready_to_schedule(approvals=approvals, term_id=term_id)
            app.logger.info(f'Prepare to schedule recordings for {len(ready_to_schedule)} courses.')
            for course in ready_to_schedule:
                section_id = int(course['sectionId'])
                _schedule_recordings(
                    all_approvals=approvals_per_section_id[section_id],
                    course=course,
                )

    @classmethod
    def description(cls):
        return 'With Kaltura API, schedule recordings and link them to Canvas sites.'


def _schedule_recordings(all_approvals, course):
    term_id = course['termId']
    section_id = int(course['sectionId'])
    all_approvals.sort(key=lambda a: a.created_at.isoformat())
    approval = all_approvals[-1]
    room = Room.get_room(approval.room_id)

    if room.kaltura_resource_id:
        # Query for date objects.
        meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
            term_id=term_id,
            section_id=section_id,
        )
        # Recording starts X minutes before/after official start; it ends Y minutes before/after official end time.
        days = format_days(meeting_days)
        adjusted_start_time = _adjust_time(meeting_start_time, app.config['KALTURA_RECORDING_OFFSET_START'])
        adjusted_end_time = _adjust_time(meeting_end_time, app.config['KALTURA_RECORDING_OFFSET_END'])

        app.logger.info(f"""
            Prepare to schedule recordings for {course['label']}:
                Room: {room.location}
                Instructor UIDs: {[instructor['uid'] for instructor in course['instructors']]}
                Schedule: {days}, {adjusted_start_time} to {adjusted_end_time}
                Recording: {approval.recording_type}; {approval.publish_type}
        """)
        Kaltura().schedule_recording(
            course_label=course['label'],
            instructors=course['instructors'],
            days=days,
            start_time=adjusted_start_time,
            end_time=adjusted_end_time,
            publish_type=approval.publish_type,
            recording_type=approval.recording_type,
            room=room,
            term_id=term_id,
        )
        scheduled = Scheduled.create(
            instructor_uids=[i['uid'] for i in course['instructors']],
            meeting_days=meeting_days,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            publish_type_=approval.publish_type,
            recording_type_=approval.recording_type,
            room_id=room.id,
            section_id=section_id,
            term_id=term_id,
        )
        notify_instructors_recordings_scheduled(course=course, scheduled=scheduled)

        uids = [approval.approved_by_uid for approval in all_approvals]
        app.logger.info(f'Recordings scheduled for course {section_id} per approvals: {", ".join(uids)}')

    else:
        app.logger.error(f"""
            FAILED to schedule recordings because room has no 'kaltura_resource_id'.
            Course: {course}
            Room: {room}
            Latest approval: {approval}
        """)


def _get_courses_ready_to_schedule(approvals, term_id):
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


def _adjust_time(military_time, offset_minutes):
    hour_and_minutes = military_time.split(':')
    return datetime.combine(
        date.today(),
        time(int(hour_and_minutes[0]), int(hour_and_minutes[1])),
    ) + timedelta(minutes=offset_minutes)
