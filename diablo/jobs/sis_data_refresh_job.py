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

from diablo.externals.rds import execute
from diablo.jobs.base_job import BaseJob
from diablo.jobs.errors import BackgroundJobError
from diablo.jobs.util import insert_or_update_instructors, refresh_cross_listings, refresh_rooms
from diablo.lib.berkeley import are_scheduled_dates_obsolete, are_scheduled_times_obsolete, get_recording_end_date, get_recording_start_date,\
    serialize_scheduled_meeting_time, serialize_sis_meeting_time
from diablo.lib.db import resolve_sql_template
from diablo.lib.util import safe_strftime
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES, SisSection
from flask import current_app as app


class SisDataRefreshJob(BaseJob):

    def _run(self, args=None):
        resolved_ddl_rds = resolve_sql_template('update_rds_sis_sections.template.sql')
        if execute(resolved_ddl_rds):
            term_id = app.config['CURRENT_TERM_ID']
            self.after_sis_data_refresh(term_id)
            _queue_schedule_updates(term_id)
        else:
            raise BackgroundJobError('Failed to update RDS indexes for intermediate schema.')

    @classmethod
    def description(cls):
        return 'Get latest course, instructor and room data from the Data Lake.'

    @classmethod
    def key(cls):
        return 'sis_data_refresh'

    @classmethod
    def after_sis_data_refresh(cls, term_id):
        distinct_instructor_uids = SisSection.get_distinct_instructor_uids()
        insert_or_update_instructors(distinct_instructor_uids)
        app.logger.info(f'{len(distinct_instructor_uids)} instructors updated')

        refresh_rooms()
        app.logger.info('RDS indexes updated.')

        refresh_cross_listings(term_id=term_id)
        app.logger.info('Cross-listings updated.')


def _queue_schedule_updates(term_id):
    for course in SisSection.get_course_changes(term_id=term_id, filter_on_obsolete=False):
        _queue_meeting_updates(course)
        _queue_instructor_updates(course)


def _queue_meeting_updates(course):
    if course['deletedAt']:
        meetings = []
    else:
        meetings = course.get('meetings', {}).get('eligible', [])

    unmatched_sis_meetings = []
    unmatched_scheduled_meetings = []

    def _matched(meeting, scheduled):
        return all([
            not are_scheduled_dates_obsolete(meeting=meeting, scheduled=scheduled),
            not are_scheduled_times_obsolete(meeting=meeting, scheduled=scheduled),
            meeting.get('room', {}).get('id') == scheduled.get('room', {}).get('id'),
        ])

    for scheduled in (course['scheduled'] or []):
        matching_meeting = next((m for m in meetings if _matched(m, scheduled)), None)
        if not matching_meeting:
            unmatched_scheduled_meetings.append(scheduled)
    for meeting in meetings:
        matching_scheduled = next((s for s in (course['scheduled'] or []) if _matched(meeting, s)), None)
        if not matching_scheduled:
            unmatched_sis_meetings.append(scheduled)

    def _serialize_sis_meeting_pattern(m):
        return json.dumps({
            'roomId': m.get('room', {}).get('id'),
            'meetingTime': serialize_sis_meeting_time(m),
            'startDate': safe_strftime(get_recording_start_date(m, return_today_if_past_start=False), '%Y-%m-%d'),
            'endDate': safe_strftime(get_recording_end_date(m), '%Y-%m-%d'),
        })

    def _serialize_scheduled_meeting_pattern(s):
        return json.dumps({
            'roomId': s.get('room', {}).get('id'),
            'meetingTime': serialize_scheduled_meeting_time(s),
            'startDate': s['meetingStartDate'],
            'endDate': s['meetingEndDate'],
        })

    unmatched_pair_count = max(len(unmatched_sis_meetings), len(unmatched_scheduled_meetings))
    for i in range(unmatched_pair_count):
        meeting = unmatched_sis_meetings[i] if i < len(unmatched_sis_meetings) else None
        scheduled = unmatched_scheduled_meetings[i] if i < len(unmatched_scheduled_meetings) else None
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='recording_schedule',
            field_value_old=(_serialize_scheduled_meeting_pattern(scheduled) if scheduled else None),
            field_value_new=(_serialize_sis_meeting_pattern(meeting) if meeting else None),
            kaltura_schedule_id=(scheduled['kalturaScheduleId'] if scheduled else None),
        )


def _queue_instructor_updates(course):
    instructors = list(filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES and not i['deletedAt'], course['instructors']))
    collaborators = list(filter(lambda i: i['roleCode'] == 'APRX' and not i['deletedAt'], course['instructors']))
    collaborator_uids = set(c['uid'] for c in collaborators)

    scheduled_instructor_uids = course['scheduled'][0].get('instructorUids', [])
    scheduled_collaborator_uids = course['scheduled'][0].get('collaboratorUids', [])

    if set(i['uid'] for i in instructors) != set(scheduled_instructor_uids):
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='instructor_uids',
            field_value_old=scheduled_instructor_uids,
            field_value_new=[i['uid'] for i in instructors],
        )

    collaborator_uids_to_add = set()
    for c in collaborators:
        if c['uid'] not in scheduled_collaborator_uids:
            previous_manual_removal = ScheduleUpdate.find_collaborator_removed(
                term_id=course['termId'],
                section_id=course['sectionId'],
                collaborator_uid=c['uid'],
            )
            if not previous_manual_removal:
                collaborator_uids_to_add.add(c['uid'])

    collaborator_uids_to_remove = set()
    for u in scheduled_collaborator_uids:
        if u not in collaborator_uids:
            previous_manual_addition = ScheduleUpdate.find_collaborator_added(
                term_id=course['termId'],
                section_id=course['sectionId'],
                collaborator_uid=c['uid'],
            )
            if not previous_manual_addition:
                collaborator_uids_to_remove.add(c['uid'])

    if len(collaborator_uids_to_add) or len(collaborator_uids_to_remove):
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='instructor_uids',
            field_value_old=scheduled_collaborator_uids,
            field_value_new=list(set(scheduled_collaborator_uids) + collaborator_uids_to_add - collaborator_uids_to_remove),
        )
