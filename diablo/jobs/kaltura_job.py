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
import traceback

from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import get_eligible_unscheduled_courses, remove_blackout_events, schedule_recordings
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date, term_name_for_sis_id
from diablo.lib.kaltura_util import get_series_description
from diablo.merged.emailer import send_system_error_email
from diablo.models.course_preference import CoursePreference
from diablo.models.email_template import EmailTemplate
from diablo.models.instructor import instructor_json_from_uids
from diablo.models.queued_email import QueuedEmail
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.scheduled import is_meeting_in_session, Scheduled
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES, SisSection
from flask import current_app as app


class KalturaJob(BaseJob):

    def _run(self):
        _schedule_new_courses()
        _update_already_scheduled_events()

    @classmethod
    def description(cls):
        return f"""
            This job:
            <ul>
                <li>Schedules recordings via Kaltura API</li>
                <li>Queues up '{EmailTemplate.get_template_type_options()['new_class_scheduled']}' emails</li>
                <li>Updates existing schedules in Kaltura</li>
            </ul>
        """

    @classmethod
    def key(cls):
        return 'kaltura'


def _get_subset_of_instructors(section_id, term_id, uids, include_deleted=False):
    course = SisSection.get_course(
        include_deleted=include_deleted,
        section_id=section_id,
        term_id=term_id,
    )
    return list(filter(lambda instructor: instructor['uid'] in uids, course['instructors']))


def _schedule_new_courses():
    term_id = app.config['CURRENT_TERM_ID']
    unscheduled_courses = get_eligible_unscheduled_courses(term_id)
    app.logger.info(f'Preparing to schedule recordings for {len(unscheduled_courses)} courses.')
    for course in unscheduled_courses:
        if course['hasOptedOut']:
            continue
        schedule_recordings(course, remove_blackout_conflicts=True, send_notifications=True)


def _update_already_scheduled_events():  # noqa C901
    kaltura = Kaltura(disable_entitlements=True)
    term_id = app.config['CURRENT_TERM_ID']
    for section_id, schedule_updates in ScheduleUpdate.get_queued_by_section_id(term_id=term_id).items():
        course = SisSection.get_course(term_id=term_id, section_id=section_id, include_deleted=True)
        if not course:
            app.logger.error(f'Course not found in SIS data (term {term_id}, section {section_id})')
            for su in schedule_updates:
                su.mark_error()
            continue

        # Schedule updates may require the Kaltura series to be deleted and recreated, and will not be processed if recording is currently underway.
        is_currently_recording = False
        for scheduled in course['scheduled'] or []:
            if is_meeting_in_session(scheduled):
                is_currently_recording = True
                break
        if is_currently_recording:
            app.logger.info(f"{course['label']}: skipping queued schedule updates because class is currently in session")
            continue

        app.logger.info(f"Preparing schedule update for {course['courseName']} {course['instructionFormat']} "
                        f"{course ['sectionNum']} (term {term_id}, section {section_id})")

        # Values common to all meeting patterns for a course.
        updated_instructor_uids = None
        updated_collaborator_uids = None
        updated_publish_type = None
        updated_recording_type = None
        updated_canvas_site_ids = None

        no_longer_eligible = False
        no_longer_scheduled = False

        publish_to_course_sites = False

        # Track individual meeting patterns.
        meetings_added = []
        meetings_removed_by_schedule_id = {}
        meetings_updated_by_schedule_id = {}

        for schedule_update in schedule_updates:
            if schedule_update.field_name == 'collaborator_uids':
                updated_collaborator_uids = schedule_update.deserialize('field_value_new')
            elif schedule_update.field_name == 'instructor_uids':
                updated_instructor_uids = schedule_update.deserialize('field_value_new')
            elif schedule_update.field_name == 'publish_type':
                updated_publish_type = schedule_update.field_value_new
            elif schedule_update.field_name == 'recording_type':
                updated_recording_type = schedule_update.field_value_new
            elif schedule_update.field_name == 'canvas_site_ids':
                updated_canvas_site_ids = schedule_update.field_value_new
            elif schedule_update.field_name == 'meeting_added':
                meetings_added.append(schedule_update)
            elif schedule_update.field_name == 'meeting_removed':
                meetings_removed_by_schedule_id[schedule_update.kaltura_schedule_id] = schedule_update.deserialize('field_value_new')
            elif schedule_update.field_name == 'meeting_updated':
                meetings_updated_by_schedule_id[schedule_update.kaltura_schedule_id] = schedule_update.deserialize('field_value_new')
            elif schedule_update.field_name == 'not_scheduled':
                no_longer_scheduled = True
            elif schedule_update.field_name == 'opted_out':
                no_longer_scheduled = True if schedule_update.field_value_new is not None else False
            elif schedule_update.field_name == 'room_not_eligible':
                no_longer_eligible = True

        for meeting_added in meetings_added:
            _handle_meeting_added(course, meeting_added, updated_publish_type, updated_recording_type, updated_collaborator_uids)

        for scheduled in course['scheduled'] or []:
            kaltura_schedule = kaltura.get_event(event_id=scheduled['kalturaScheduleId'])
            scheduled_model = Scheduled.get_by_id(scheduled['id'])
            if kaltura_schedule:
                if no_longer_scheduled or no_longer_eligible or scheduled['kalturaScheduleId'] in meetings_removed_by_schedule_id:
                    _handle_meeting_removed(kaltura, course, scheduled, schedule_updates)
                    continue

                if updated_collaborator_uids is not None or updated_instructor_uids is not None:
                    _handle_instructor_updates(
                        kaltura, course, scheduled, scheduled_model, schedule_updates, kaltura_schedule, updated_collaborator_uids,
                        updated_instructor_uids,
                    )

                if updated_recording_type:
                    scheduled_model.update(recording_type=updated_recording_type)

                if scheduled['publishType'] and scheduled['publishType'].startswith('kaltura_media_gallery'):
                    if scheduled['publishType'] == 'kaltura_media_gallery_moderated':
                        publish_to_course_sites = 'moderated'
                    else:
                        publish_to_course_sites = 'unmoderated'
                else:
                    publish_to_course_sites = None

                if scheduled['kalturaScheduleId'] in meetings_updated_by_schedule_id:
                    _handle_meeting_updates(
                        kaltura,
                        meetings_updated_by_schedule_id,
                        scheduled['kalturaScheduleId'],
                        scheduled_model,
                        schedule_updates,
                    )
            else:
                app.logger.warn(f"The previously scheduled {course['label']} schedule id {scheduled['kalturaScheduleId']} was not found in Kaltura.")

        if updated_publish_type:
            publish_to_course_sites = _handle_publish_type_update(updated_publish_type, scheduled_model)

        if updated_publish_type or updated_canvas_site_ids:
            update_options = _construct_schedule_update_options(course, updated_publish_type, updated_recording_type, updated_collaborator_uids)
            updated_canvas_site_ids = _handle_course_site_categories(
                kaltura,
                course,
                publish_to_course_sites,
                schedule_updates,
                update_options,
            )

        _mark_success(
            schedule_updates,
            (
                'publish_type',
                'recording_type',
                'instructor_uids',
                'collaborator_uids',
                'canvas_site_ids',
                'not_scheduled',
                'opted_out',
                'room_not_eligible',
            ),
        )

        if no_longer_scheduled:
            QueuedEmail.notify_instructors_no_longer_scheduled(course)
        elif no_longer_eligible:
            QueuedEmail.notify_instructors_no_longer_eligible(course)
        else:
            scheduled = (course['scheduled'] or [{}])[0]
            if updated_publish_type or\
                    updated_recording_type or\
                    updated_collaborator_uids is not None or\
                    updated_canvas_site_ids is not None:
                collaborator_uids = updated_collaborator_uids
                if collaborator_uids is None:
                    collaborator_uids = scheduled.get('collaboratorUids', [])

                canvas_site_ids = updated_canvas_site_ids
                if canvas_site_ids is None:
                    canvas_site_ids = scheduled.get('canvasSiteIds', [])

                QueuedEmail.notify_instructors_changes_confirmed(
                    course,
                    collaborator_uids=collaborator_uids,
                    canvas_site_ids=canvas_site_ids,
                    publish_type=updated_publish_type or scheduled.get('publishType'),
                    recording_type=updated_recording_type or scheduled.get('recordingType'),
                )
            if meetings_added or meetings_removed_by_schedule_id or meetings_updated_by_schedule_id:
                QueuedEmail.notify_instructors_schedule_change(course)
            if updated_instructor_uids:
                previously_scheduled_instructor_uids = scheduled.get('instructorUids') or []
                added_instructor_uids = [i for i in updated_instructor_uids if i not in previously_scheduled_instructor_uids]
                removed_instructor_uids = [i for i in previously_scheduled_instructor_uids if i not in updated_instructor_uids]
                if added_instructor_uids:
                    for instructor in instructor_json_from_uids(added_instructor_uids):
                        QueuedEmail.notify_instructor_added(instructor, course)
                if removed_instructor_uids:
                    for instructor in instructor_json_from_uids(removed_instructor_uids):
                        QueuedEmail.notify_instructor_removed(instructor, course)


def _handle_instructor_updates(
    kaltura, course, scheduled, scheduled_model, schedule_updates, kaltura_schedule,
    updated_collaborator_uids, updated_instructor_uids,
):
    instructors = [i for i in course['instructors'] if i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES and not i['deletedAt']]
    instructor_uids = [i['uid'] for i in instructors]
    if updated_collaborator_uids is None:
        collaborator_uids = scheduled['collaboratorUids']
    else:
        collaborator_uids = updated_collaborator_uids

    uids_entitled_to_edit = list(set(instructor_uids + collaborator_uids))
    description = get_series_description(
        course_label=course['label'],
        instructors=instructors,
        term_name=term_name_for_sis_id(course['termId']),
    )

    try:
        kaltura.update_base_entry(
            description=description,
            entry_id=kaltura_schedule['templateEntryId'],
            name=kaltura_schedule.get('name'),
            uids_entitled_to_edit=uids_entitled_to_edit,
            uids_entitled_to_publish=uids_entitled_to_edit,
        )
        kaltura.update_schedule_event(scheduled_model, description=description)
        scheduled_model.update(instructor_uids=instructor_uids, collaborator_uids=collaborator_uids)
        CoursePreference.update_collaborator_uids(
            term_id=course['termId'],
            section_id=course['sectionId'],
            collaborator_uids=collaborator_uids,
        )
    except Exception as e:
        _mark_error(
            schedule_updates,
            e,
            ('collaborator_uids', 'instructor_uids'),
            f"Failed to update Kaltura base entry: {kaltura_schedule['templateEntryId']}",
        )


def _handle_meeting_added(course, meeting_added, updated_publish_type, updated_recording_type, updated_collaborator_uids):
    meeting = meeting_added.deserialize('field_value_new')
    updates = _construct_schedule_update_options(course, updated_publish_type, updated_recording_type, updated_collaborator_uids)

    newly_scheduled = schedule_recordings(
        {**course, **{'meetings': {'eligible': [meeting]}}},
        remove_blackout_conflicts=True,
        send_notifications=True,
        updates=updates,
    )
    if newly_scheduled:
        meeting_added.mark_success()
        course['scheduled'].append(newly_scheduled[0].to_api_json())
    else:
        meeting_added.mark_error()


def _handle_meeting_removed(kaltura, course, scheduled, schedule_updates):
    try:
        kaltura.delete(scheduled['kalturaScheduleId'])
        Scheduled.delete(term_id=course['termId'], section_id=course['sectionId'], kaltura_schedule_id=scheduled['kalturaScheduleId'])
        _mark_success(schedule_updates, 'meeting_removed', scheduled['kalturaScheduleId'])
    except Exception as e:
        _mark_error(
            schedule_updates,
            e,
            f"Failed to delete Kaltura schedule: {scheduled['kalturaScheduleId']}",
            'meeting_removed',
            kaltura_schedule_id=scheduled['kalturaScheduleId'],
        )
        _mark_error(schedule_updates, e, None, ('not_scheduled', 'opted_out', 'room_not_eligible'))


def _handle_meeting_updates(kaltura, meetings_updated_by_schedule_id, kaltura_schedule_id, scheduled_model, schedule_updates):
    meeting = meetings_updated_by_schedule_id[kaltura_schedule_id]
    try:
        kaltura.update_schedule_event(scheduled_model, meeting_attributes=meeting)
        if 'days' in meeting:
            scheduled_model.update(
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                meeting_start_time=meeting['startTime'],
            )
            remove_blackout_events(kaltura_schedule_id=scheduled_model.kaltura_schedule_id)
        if 'room' in meeting:
            scheduled_model.update(
                room_id=meeting['room']['id'],
            )
        _mark_success(schedule_updates, 'meeting_updated', kaltura_schedule_id)
    except Exception as e:
        _mark_error(schedule_updates, e, f'Failed to update Kaltura schedule: {kaltura_schedule_id}', 'meeting_updated', kaltura_schedule_id)


def _handle_publish_type_update(updated_publish_type, scheduled_model):
    if updated_publish_type == 'kaltura_media_gallery':
        scheduled_model.update(publish_type='kaltura_media_gallery')
        publish_to_course_sites = 'unmoderated'
    elif updated_publish_type == 'kaltura_my_media':
        scheduled_model.update(publish_type='kaltura_my_media')
        publish_to_course_sites = None
    return publish_to_course_sites


def _handle_course_site_categories(kaltura, course, publish_to_course_sites, schedule_updates, update_options):  # noqa C901
    if publish_to_course_sites and course['canvasSiteIds']:
        updated_canvas_site_ids = course['canvasSiteIds']
    else:
        updated_canvas_site_ids = []

    diablo_category_names = set(str(site_id) for site_id in updated_canvas_site_ids)
    common_category = kaltura.get_category_object(name=app.config['KALTURA_COMMON_CATEGORY'])

    schedule_ids_to_update = []
    schedule_deletion_required = False

    for scheduled in course['scheduled'] or []:
        try:
            kaltura_schedule = kaltura.get_event(event_id=scheduled['kalturaScheduleId'])
            template_entry_id = kaltura_schedule['templateEntryId']
            kaltura_categories = kaltura.get_categories(template_entry_id) or []
            kaltura_category_names = set(c['name'] for c in kaltura_categories if c['id'] != common_category['id'])

            if kaltura_category_names.difference(diablo_category_names):
                schedule_deletion_required = True
            elif diablo_category_names.difference(kaltura_category_names):
                schedule_ids_to_update.append(scheduled['kalturaScheduleId'])
        except Exception as e:
            _mark_error(
                schedule_updates,
                e,
                f"Failed to retrieve existing Kaltura categories from schedule {scheduled['kalturaScheduleId']}",
                'canvas_site_ids',
            )
            return None

    if not (schedule_deletion_required or schedule_ids_to_update):
        return None

    if schedule_deletion_required:
        try:
            app.logger.info(f"{course['label']}: will delete and recreate Kaltura schedule(s) to remove existing categories")
            for scheduled in course['scheduled']:
                kaltura.delete(scheduled['kalturaScheduleId'])
                Scheduled.delete(term_id=course['termId'], section_id=course['sectionId'], kaltura_schedule_id=scheduled['kalturaScheduleId'])
            rescheduled = schedule_recordings(course, send_notifications=False, updates=update_options)
            if publish_to_course_sites and updated_canvas_site_ids:
                schedule_ids_to_update = [scheduled['kalturaScheduleId'] for scheduled in rescheduled]
        except Exception as e:
            _mark_error(
                schedule_updates,
                e,
                'Failed to delete and recreate Kaltura schedules',
                'canvas_site_ids',
            )
            return None

    for kaltura_schedule_id in schedule_ids_to_update:
        try:
            kaltura_schedule = kaltura.get_event(event_id=kaltura_schedule_id)
            template_entry_id = kaltura_schedule['templateEntryId']
            kaltura_categories = kaltura.get_categories(template_entry_id) or []
            kaltura_category_names = set(c['name'] for c in kaltura_categories if c['id'] != common_category['id'])

            for canvas_course_site_id in updated_canvas_site_ids:
                if str(canvas_course_site_id) not in kaltura_category_names:
                    category = kaltura.get_or_create_canvas_category_object(canvas_course_site_id=canvas_course_site_id)
                    if category:
                        app.logger.info(f"{course['label']}: add Kaltura category for canvas_course_site {canvas_course_site_id}")
                        kaltura.add_to_kaltura_category(
                            category_id=category['id'],
                            entry_id=template_entry_id,
                        )
        except Exception as e:
            _mark_error(
                schedule_updates,
                e,
                (f'Failed to add Kaltura categories {updated_canvas_site_ids} to Kaltura series {kaltura_schedule_id}'),
                'canvas_site_ids',
            )
            return None

    return updated_canvas_site_ids


def _construct_schedule_update_options(course, updated_publish_type=None, updated_recording_type=None, updated_collaborator_uids=None):
    updates = {
        'publishType': updated_publish_type or course['scheduled'][0]['publishType'],
        'recordingType': updated_recording_type or course['scheduled'][0]['recordingType'],
    }
    if updated_collaborator_uids is None:
        updates['collaboratorUids'] = course['scheduled'][0]['collaboratorUids']
    else:
        updates['collaboratorUids'] = updated_collaborator_uids
    return updates


def _mark_success(schedule_updates, field_names, kaltura_schedule_id=None):
    for su in schedule_updates:
        if su.field_name in field_names and \
                su.status == 'queued' and \
                (kaltura_schedule_id is None or su.kaltura_schedule_id == kaltura_schedule_id):
            su.mark_success()


def _mark_error(schedule_updates, e, message, field_names, kaltura_schedule_id=None):
    if message:
        su = schedule_updates[0]
        message = f'Schedule update error: term {su.term_id}, section {su.section_id}, fields {field_names}\n' + message
        app.logger.error(message)
        app.logger.exception(e)
        send_system_error_email(
            message=f'{message}\n\n<pre>{traceback.format_exc()}</pre>',
            subject=message,
        )
    for su in schedule_updates:
        if su.field_name in field_names and \
                su.status == 'queued' and \
                (kaltura_schedule_id is None or su.kaltura_schedule_id == kaltura_schedule_id):
            su.mark_error()
