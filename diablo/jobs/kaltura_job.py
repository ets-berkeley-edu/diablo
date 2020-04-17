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
from datetime import datetime, timedelta

from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import get_courses_ready_to_schedule
from diablo.lib.util import format_days, objects_to_dict_organized_by_section_id
from diablo.merged.emailer import notify_instructors_recordings_scheduled
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
            for course in get_courses_ready_to_schedule(approvals=approvals, term_id=term_id):
                section_id = int(course['sectionId'])
                _schedule_recordings(
                    all_approvals=approvals_per_section_id[section_id],
                    course=course,
                )

    @classmethod
    def description(cls):
        return 'With Kaltura API, schedule recordings and link them to Canvas sites.'


def _schedule_recordings(all_approvals, course):
    all_approvals.sort(key=lambda a: a.created_at.isoformat())
    approval = all_approvals[-1]
    room = Room.get_room(approval.room_id)

    if room.kaltura_resource_id:
        term_id = course['termId']

        section_id = int(course['sectionId'])
        course_name = course['courseName']
        section = f'{course["instructionFormat"]} ${course["sectionNum"]} ()'
        comment = f'Recordings for {course_name} {section} scheduled by Diablo.'
        meeting_days, meeting_start_time, meeting_end_time = SisSection.get_meeting_times(
            term_id=term_id,
            section_id=section_id,
        )
        # At UC Berkeley, recording starts 7 minutes after official start and ends 2 minutes after official end time.
        time_format = '%H:%M'
        adjusted_start_time = datetime.strptime(meeting_start_time, time_format) + timedelta(minutes=7)
        adjusted_end_time = datetime.strptime(meeting_end_time, time_format) + timedelta(minutes=2)

        Kaltura().schedule_recording(
            comment=comment,
            course_name=course_name,
            instructor_uids=[instructor['uid'] for instructor in course['instructors']],
            days=format_days(meeting_days),
            start_time=adjusted_start_time,
            end_time=adjusted_end_time,
            publish_type=approval.publish_type,
            recording_type=approval.recording_type,
            room=room,
        )
        scheduled = Scheduled.create(
            section_id=section_id,
            term_id=term_id,
            instructor_uids=SisSection.get_instructor_uids(term_id=term_id, section_id=section_id),
            meeting_days=meeting_days,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            publish_type_=approval.publish_type,
            recording_type_=approval.recording_type,
            room_id=approval.room_id,
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
