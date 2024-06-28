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
import json

from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import build_merged_collaborators_list, is_valid_meeting_schedule
from diablo.lib.berkeley import are_scheduled_dates_obsolete, are_scheduled_times_obsolete, get_recording_end_date, get_recording_start_date
from diablo.lib.util import safe_strftime
from diablo.models.course_preference import CoursePreference
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES, SisSection
from flask import current_app as app


class ScheduleUpdatesJob(BaseJob):

    def _run(self, args=None):
        term_id = app.config['CURRENT_TERM_ID']
        _queue_schedule_updates(term_id)

    @classmethod
    def description(cls):
        return 'Schedule Kaltura updates based on changed SIS data.'

    @classmethod
    def key(cls):
        return 'schedule_updates'


def _queue_schedule_updates(term_id):
    for course in SisSection.get_course_changes(term_id=term_id):
        eligible_meetings = course.get('meetings', {}).get('eligible', [])
        ineligible_meetings = course.get('meetings', {}).get('ineligible', [])
        if course['deletedAt'] or (_valid_meeting_count(eligible_meetings) + _valid_meeting_count(ineligible_meetings) == 0):
            _queue_not_scheduled_update(course)
        elif _valid_meeting_count(eligible_meetings) == 0 and _valid_meeting_count(ineligible_meetings) > 0:
            _queue_room_not_eligible_update(course)
        else:
            _queue_meeting_updates(course)
            _queue_instructor_updates(course)


def _queue_not_scheduled_update(course):
    scheduled = course['scheduled'][0]
    ScheduleUpdate.queue(
        term_id=course['termId'],
        section_id=course['sectionId'],
        field_name='not_scheduled',
        field_value_old=json.dumps(scheduled),
        field_value_new=None,
    )
    _downgrade_recording_type(course)


def _queue_room_not_eligible_update(course):
    meeting = course.get('meetings', {}).get('ineligible', [])[0]
    scheduled = course['scheduled'][0]
    CoursePreference.update_recording_type(
        term_id=course['termId'],
        section_id=course['sectionId'],
        recording_type='presenter_presentation_audio',
    )
    ScheduleUpdate.queue(
        term_id=course['termId'],
        section_id=course['sectionId'],
        field_name='room_not_eligible',
        field_value_old=json.dumps(_get_room_summary(scheduled)),
        field_value_new=json.dumps(_get_room_summary(meeting)),
    )
    _downgrade_recording_type(course)


def _valid_meeting_count(meetings):
    return len([m for m in meetings if is_valid_meeting_schedule(m)])


def _queue_meeting_updates(course):
    meetings = course.get('meetings', {}).get('eligible', [])
    unmatched_sis_meetings = []
    unmatched_scheduled_meetings = []

    def _matched(meeting, scheduled):
        return all([
            not are_scheduled_dates_obsolete(meeting=meeting, scheduled=scheduled),
            not are_scheduled_times_obsolete(meeting=meeting, scheduled=scheduled),
            meeting.get('room', {}).get('id') == scheduled.get('room', {}).get('id'),
        ])

    for scheduled in course['scheduled']:
        matching_meeting = next((m for m in meetings if _matched(m, scheduled)), None)
        if not matching_meeting:
            unmatched_scheduled_meetings.append(scheduled)
    for meeting in meetings:
        matching_scheduled = next((s for s in course['scheduled'] if _matched(meeting, s)), None)
        if not matching_scheduled:
            unmatched_sis_meetings.append(meeting)

    unmatched_pair_count = max(len(unmatched_sis_meetings), len(unmatched_scheduled_meetings))
    for i in range(unmatched_pair_count):
        meeting = unmatched_sis_meetings[i] if i < len(unmatched_sis_meetings) else None
        scheduled = unmatched_scheduled_meetings[i] if i < len(unmatched_scheduled_meetings) else None

        if not scheduled and is_valid_meeting_schedule(meeting):
            ScheduleUpdate.queue(
                term_id=course['termId'],
                section_id=course['sectionId'],
                field_name='meeting_added',
                field_value_old=None,
                field_value_new=json.dumps({
                    'days': meeting['days'],
                    'startTime': meeting['startTime'],
                    'endTime': meeting['endTime'],
                    'startDate': safe_strftime(get_recording_start_date(meeting, return_today_if_past_start=True), '%Y-%m-%d'),
                    'endDate': safe_strftime(get_recording_end_date(meeting), '%Y-%m-%d'),
                    'room': _get_room_summary(meeting),
                }),
            )

        elif not meeting or not is_valid_meeting_schedule(meeting):
            ScheduleUpdate.queue(
                term_id=course['termId'],
                section_id=course['sectionId'],
                field_name='meeting_removed',
                field_value_old=json.dumps({
                    'days': ''.join(scheduled['meetingDays']),
                    'startTime': scheduled['meetingStartTime'],
                    'endTime': scheduled['meetingEndTime'],
                    'startDate': scheduled['meetingStartDate'],
                    'endDate': scheduled['meetingEndDate'],
                    'room': _get_room_summary(scheduled),
                }),
                field_value_new=None,
                kaltura_schedule_id=scheduled['kalturaScheduleId'],
            )

        else:
            meeting_old = {}
            meeting_new = {}

            if are_scheduled_dates_obsolete(meeting=meeting, scheduled=scheduled) or \
                    are_scheduled_times_obsolete(meeting=meeting, scheduled=scheduled):
                meeting_old = {
                    'days': ''.join(scheduled['meetingDays']),
                    'startTime': scheduled['meetingStartTime'],
                    'endTime': scheduled['meetingEndTime'],
                    'startDate': scheduled['meetingStartDate'],
                    'endDate': scheduled['meetingEndDate'],
                }
                meeting_new = {
                    'days': meeting['days'],
                    'startTime': meeting['startTime'],
                    'endTime': meeting['endTime'],
                    'startDate': safe_strftime(get_recording_start_date(meeting, return_today_if_past_start=True), '%Y-%m-%d'),
                    'endDate': safe_strftime(get_recording_end_date(meeting), '%Y-%m-%d'),
                }
            if meeting.get('room', {}).get('id') != scheduled.get('room', {}).get('id'):
                meeting_old.update({'room': _get_room_summary(scheduled)})
                meeting_new.update({'room': _get_room_summary(meeting)})

                # Downgrade recording type if moving out of an auditorium.
                if scheduled['recordingType'] == 'presenter_presentation_audio_with_operator' and not _is_in_auditorium(meeting):
                    ScheduleUpdate.queue(
                        term_id=course['termId'],
                        section_id=course['sectionId'],
                        field_name='recording_type',
                        field_value_old='presenter_presentation_audio_with_operator',
                        field_value_new='presenter_presentation_audio',
                    )
                    _downgrade_recording_type(course)

            ScheduleUpdate.queue(
                term_id=course['termId'],
                section_id=course['sectionId'],
                field_name='meeting_updated',
                field_value_old=json.dumps(meeting_old),
                field_value_new=json.dumps(meeting_new),
                kaltura_schedule_id=scheduled['kalturaScheduleId'],
            )


def _queue_instructor_updates(course):
    instructors = list(filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES and not i['deletedAt'], course['instructors']))
    scheduled_instructor_uids = course['scheduled'][0].get('instructorUids') or []

    if set(i['uid'] for i in instructors) != set(scheduled_instructor_uids):
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='instructor_uids',
            field_value_old=scheduled_instructor_uids,
            field_value_new=[i['uid'] for i in instructors],
        )

    scheduled_collaborator_uids = course['scheduled'][0].get('collaboratorUids') or []
    new_collaborator_uids = build_merged_collaborators_list(course, scheduled_collaborator_uids)

    if new_collaborator_uids != set(scheduled_collaborator_uids):
        new_collaborator_uids = list(new_collaborator_uids)
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='collaborator_uids',
            field_value_old=scheduled_collaborator_uids,
            field_value_new=new_collaborator_uids,
        )
        CoursePreference.update_collaborator_uids(
            term_id=course['termId'],
            section_id=course['sectionId'],
            collaborator_uids=new_collaborator_uids,
        )


def _downgrade_recording_type(course):
    # When a course moves out of an auditorium, or loses its room entirely, ensure recording_type is set to the default
    # (without operator), since the with-operator setting requires the course to be located in an auditorium.
    # Other user-set preferences (publish type and collaborator UIDs) should persist through unscheduling, since they may
    # later be rescheduled.
    CoursePreference.update_recording_type(
        term_id=course['termId'],
        section_id=course['sectionId'],
        recording_type='presenter_presentation_audio',
    )


def _is_in_auditorium(meeting):
    room = meeting.get('room')
    if room and 'presenter_presentation_audio_with_operator' in room.get('recordingTypeOptions', {}):
        return True
    return False


def _get_room_summary(meeting):
    room = meeting.get('room')
    if not room:
        return None
    else:
        return {
            'id': room['id'],
            'location': room['location'],
            'kalturaResourceId': room['kalturaResourceId'],
        }
