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
from itertools import islice
import re
import traceback

from diablo import db, std_commit
from diablo.externals.kaltura import CREATED_BY_DIABLO_TAG, Kaltura
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from diablo.lib.kaltura_util import represents_recording_series
from diablo.lib.util import localize_datetime, utc_now
from diablo.merged.calnet import get_calnet_users_for_uids
from diablo.merged.emailer import send_system_error_email
from diablo.models.blackout import Blackout
from diablo.models.course_preference import CoursePreference
from diablo.models.cross_listing import CrossListing
from diablo.models.instructor import Instructor
from diablo.models.opt_out import OptOut
from diablo.models.queued_email import notify_instructors_recordings_scheduled
from diablo.models.room import Room
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES, SisSection
from flask import current_app as app
from KalturaClient.Plugins.Schedule import KalturaScheduleEventRecurrenceType
from sqlalchemy import text


def build_merged_collaborators_list(course, manually_set_collaborator_uids):
    # On the SIS side, pick up anyone who's an administrative proxy.
    sis_collaborators = list(filter(lambda i: i['roleCode'] == 'APRX' and not i['deletedAt'], course['instructors']))
    sis_collaborator_uids = set(c['uid'] for c in sis_collaborators)

    if not manually_set_collaborator_uids:
        return sis_collaborator_uids

    # Compare to our most recent list of manually set collaborators on the Diablo/Kaltura side. If we have a SIS collaborator
    # who doesn't show up in that last, add them unless they've been manually removed.
    collaborator_uids_to_add = set()
    for c in sis_collaborators:
        if c['uid'] not in manually_set_collaborator_uids:
            previous_manual_removal = ScheduleUpdate.find_collaborator_removed(
                term_id=course['termId'],
                section_id=course['sectionId'],
                collaborator_uid=c['uid'],
            )
            if not previous_manual_removal:
                collaborator_uids_to_add.add(c['uid'])

    # Run the same comparison, removing any collaborator who's not present in SIS and was not manually added.
    collaborator_uids_to_remove = set()
    for u in manually_set_collaborator_uids:
        if u not in sis_collaborator_uids:
            previous_manual_addition = ScheduleUpdate.find_collaborator_added(
                term_id=course['termId'],
                section_id=course['sectionId'],
                collaborator_uid=u,
            )
            if not previous_manual_addition:
                collaborator_uids_to_remove.add(u)

    if len(collaborator_uids_to_add) or len(collaborator_uids_to_remove):
        return set(manually_set_collaborator_uids).union(collaborator_uids_to_add).difference(collaborator_uids_to_remove)
    else:
        return set(manually_set_collaborator_uids)


def get_eligible_unscheduled_courses(term_id):
    return SisSection.get_courses(
        exclude_scheduled=True,
        include_administrative_proxies=True,
        term_id=term_id,
    )


def insert_or_update_instructors(instructor_uids):
    instructors = []
    for instructor in get_calnet_users_for_uids(app=app, uids=instructor_uids).values():
        instructors.append({
            'dept_code': instructor.get('deptCode'),
            'email': instructor.get('email'),
            'first_name': instructor.get('firstName') or '',
            'last_name': instructor.get('lastName') or '',
            'uid': instructor['uid'],
        })

    Instructor.upsert(instructors)


def is_valid_meeting_schedule(meeting):
    for key in ['days', 'startTime', 'endTime', 'startDate', 'endDate']:
        if not meeting.get(key):
            return False
    return True


def refresh_rooms():
    locations = SisSection.get_distinct_meeting_locations()
    existing_locations = Room.get_all_locations()
    new_locations = [location for location in locations if location not in existing_locations]
    if new_locations:
        app.logger.info(f'Creating {len(new_locations)} new rooms')
        for location in new_locations:
            Room.create(location=location)

    def _normalize(room_location):
        return re.sub(r'[\W_]+', '', room_location).lower()
    kaltura_resource_ids_per_room = {}
    all_rooms = Room.all_rooms()
    for resource in Kaltura().get_schedule_resources():
        location = _normalize(resource['name'])
        if location:
            for room in all_rooms:
                if _normalize(room.location) == location:
                    kaltura_resource_ids_per_room[room.id] = resource['id']
                    break

    if kaltura_resource_ids_per_room:
        Room.update_kaltura_resource_mappings(kaltura_resource_ids_per_room)


def refresh_cross_listings(term_id):
    # Populate 'cross_listings' table: If {123, 234, 345} is a set of cross-listed section_ids then:
    #  1. Section 123 will have a record in the 'sis_sections' table; 234 and 345 will not.
    #  2. The cross-listings table will get 123: [234, 345]
    #  3. We collapse the names of the three section into a single name/title for section 123

    # IMPORTANT: These will be ordered by schedule (time and location)
    sql = """
                SELECT
                    section_id,
                    trim(concat(
                        meeting_days,
                        meeting_end_date,
                        meeting_end_time,
                        meeting_location,
                        meeting_start_date,
                        meeting_start_time
                    )) as schedule
                FROM sis_sections
                WHERE
                    term_id = :term_id
                    AND meeting_days <> ''
                    AND meeting_end_date IS NOT NULL
                    AND meeting_end_time <> ''
                    AND meeting_location IS NOT NULL
                    AND meeting_location NOT IN ('', 'Internet/Online', 'Off Campus', 'Requested General Assignment')
                    AND meeting_start_date IS NOT NULL
                    AND meeting_start_time <> ''
                    AND deleted_at IS NULL
                ORDER BY schedule, section_id
            """
    rows = []
    for row in db.session.execute(text(sql), {'term_id': term_id}):
        rows.append({'schedule': row['schedule'], 'section_id': row['section_id']})
    register_cross_listings(rows, term_id)


def register_cross_listings(rows, term_id):  # noqa C901
    cross_listings = {}
    previous_schedule = None
    primary_section = None

    for row in rows:
        section_id = row['section_id']
        schedule = row['schedule']
        if section_id not in cross_listings:
            if schedule == previous_schedule:
                primary_schedule = primary_section['schedule']
                primary_section_id = primary_section['section_id']
                if section_id not in cross_listings[primary_section_id] and schedule == primary_schedule:
                    cross_listings[primary_section_id].append(section_id)
            else:
                primary_section = row
                cross_listings[primary_section['section_id']] = []
        previous_schedule = schedule

    # Toss out section_ids with no cross-listings
    for section_id, section_ids in cross_listings.copy().items():
        if not section_ids:
            cross_listings.pop(section_id)

    # These tables link by section id to the principal cross-listing only.
    principal_listing_linked_tables = ('queued_emails', 'schedule_updates', 'scheduled')
    # These tables link by section id to all cross-listings.
    all_listing_linked_tables = ('course_preferences', 'opt_outs')

    # Before refreshing the cross-listing table, update any Diablo tables pointing to deleted sections
    # that were cross-listed with extant sections.
    for table in principal_listing_linked_tables:
        update_deleted_principal_listing_references(term_id, table)

    # Prepare for refresh by deleting old rows
    db.session.execute(CrossListing.__table__.delete().where(CrossListing.term_id == term_id))

    def chunks(data, chunk_size=500):
        iterator = iter(data)
        for i in range(0, len(data), chunk_size):
            yield {k: data[k] for k in islice(iterator, chunk_size)}

    non_principal_section_ids = []

    for cross_listings_chunk in chunks(cross_listings):
        cross_listing_count = len(cross_listings_chunk)
        query = 'INSERT INTO cross_listings (term_id, section_id, cross_listed_section_ids, created_at) VALUES'
        for index, (section_id, cross_listed_section_ids) in enumerate(cross_listings_chunk.items()):
            query += f' (:term_id, {section_id}, ' + "'{" + _join(cross_listed_section_ids, ', ') + "}', now())"
            if index < cross_listing_count - 1:
                query += ','
            non_principal_section_ids.extend(cross_listed_section_ids)
        db.session.execute(query, {'term_id': term_id})

    # Mark cross-listed section_ids as non-principal listings to keep duplicate results out of SisSection queries.
    SisSection.set_non_principal_listings(section_ids=non_principal_section_ids, term_id=term_id)

    # Update any Diablo tables pointing to no-longer-principal section listings.
    for table in principal_listing_linked_tables:
        update_no_longer_principal_listing_references(term_id, table)

    # Add in any needed Diablo table rows for entirely new cross-listings.
    for section_id, section_ids in cross_listings.items():
        all_section_ids = section_ids + [section_id]
        for tablename in all_listing_linked_tables:
            update_new_cross_listings(term_id, all_section_ids, tablename)

    std_commit()
    return cross_listings


def update_deleted_principal_listing_references(term_id, tablename):
    # Handle references to deleted sections cross-listed with extant sections.
    sql = f"""UPDATE {tablename} t1
        SET section_id = cl_lookups.section_id
        FROM sis_sections ss
        JOIN (SELECT ss2.term_id, ss2.section_id, cl.section_id AS cl_section_id
            FROM cross_listings cl
            JOIN sis_sections ss2
                ON ss2.term_id = cl.term_id
                AND ss2.section_id = ANY(cl.cross_listed_section_ids) AND ss2.deleted_at IS NULL) cl_lookups
        ON ss.term_id = :term_id AND ss.term_id = cl_lookups.term_id AND ss.section_id = cl_lookups.cl_section_id AND ss.deleted_at IS NOT NULL
        WHERE t1.term_id = ss.term_id AND t1.section_id = ss.section_id"""
    db.session.execute(text(sql), {'term_id': term_id})


def update_no_longer_principal_listing_references(term_id, tablename):
    # Handle references to extant sections that are no longer the principal cross-listing.
    sql = f"""UPDATE {tablename} t1
        SET section_id = cl_lookups.section_id
        FROM sis_sections ss
        JOIN (SELECT term_id, section_id, UNNEST(cross_listed_section_ids) AS cl_section_id FROM cross_listings) cl_lookups
            ON ss.term_id = :term_id AND ss.term_id = cl_lookups.term_id AND ss.section_id = cl_lookups.cl_section_id
        WHERE t1.term_id = ss.term_id AND t1.section_id = ss.section_id"""
    db.session.execute(text(sql), {'term_id': term_id})


def update_new_cross_listings(term_id, section_ids, tablename):
    # Copy preferences and opt-out settings to any newly added cross-listings.
    sql = f'SELECT * FROM {tablename} WHERE term_id = :term_id AND section_id = ANY(:section_ids)'
    rows = list(db.session.execute(text(sql), {'term_id': term_id, 'section_ids': section_ids}))
    if not rows:
        return
    new_section_ids = set(section_ids) - set(r['section_id'] for r in rows)
    for new_section_id in new_section_ids:
        if tablename == 'course_preferences':
            db.session.add(CoursePreference(
                term_id=term_id,
                section_id=new_section_id,
                publish_type=rows[0]['publish_type'],
                recording_type=rows[0]['recording_type'],
                canvas_site_ids=rows[0]['canvas_site_ids'],
                collaborator_uids=rows[0]['collaborator_uids'],
            ))
        elif tablename == 'opt_outs':
            db.session.add(OptOut(
                term_id=term_id,
                section_id=new_section_id,
                instructor_uid=rows[0]['instructor_uid'],
            ))


def remove_blackout_events(kaltura_schedule_id=None):
    kaltura = Kaltura()
    for blackout in Blackout.all_blackouts():
        if blackout.end_date < utc_now():
            app.logger.info(f'Removing past blackout: {blackout}')
            Blackout.delete_blackout(blackout.id)
        else:
            end_date = localize_datetime(blackout.end_date)
            start_date = localize_datetime(blackout.start_date)
            events = kaltura.get_events_in_date_range(
                end_date=end_date,
                kaltura_schedule_id=kaltura_schedule_id,
                recurrence_type=KalturaScheduleEventRecurrenceType.RECURRENCE,
                start_date=start_date,
            )
            for event in events:
                created_by_diablo = CREATED_BY_DIABLO_TAG in event['tags']
                if created_by_diablo and not represents_recording_series(event):
                    kaltura.delete(event['id'])
                    app.logger.info(f"'Event {event['summary']} deleted per {blackout}.")


def schedule_recordings(course, remove_blackout_conflicts=False, send_notifications=False, updates=None):
    def _report_error(subject):
        message = f'{subject}\n\n<pre>{course}</pre>'
        app.logger.error(message)
        send_system_error_email(message=message, subject=subject)

    meetings = course.get('meetings', {}).get('eligible', [])
    if not len(meetings):
        _report_error(subject=f"{course['label']} not scheduled. No eligible meeting patterns found.")
        return None

    instructors = list(filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES and not i['deletedAt'], course['instructors']))

    # When scheduling a new course, we derive user-set properties from, in fallback order: 1) recent updates made through the UI; 2)
    # course preferences that persist in Diablo's database from an earlier instance of scheduling; 3) default values.
    if updates:
        publish_type = updates['publishType']
        recording_type = updates['recordingType']
        collaborator_uids = updates['collaboratorUids']
    else:
        publish_type = course.get('publishType') or 'kaltura_my_media'
        recording_type = course.get('recordingType') or 'presenter_presentation_audio'
        collaborator_uids = build_merged_collaborators_list(course, course.get('collaboratorUids'))

    # Add a dummy 'roleCode' type for all collaborators, whether or not they teach in SIS. This will tell downstream
    # code to give these users access in Kaltura but not include them in the series description.
    collaborators = [{'uid': collaborator_uid, 'roleCode': 'Collaborator'} for collaborator_uid in collaborator_uids]

    all_scheduled = []

    for meeting in meetings:
        location = meeting.get('room', {}).get('location')
        room = Room.find_room(location=location)
        if not room:
            _report_error(subject=f"{course['label']} not scheduled. Room {location} not found.")
            continue

        if not is_valid_meeting_schedule(meeting):
            _report_error(subject=f"{course['label']} not scheduled. Invalid SIS meeting schedule.")
            continue

        term_id = course['termId']
        section_id = int(course['sectionId'])
        if room.kaltura_resource_id:
            try:
                kaltura_schedule_id = Kaltura().schedule_recording(
                    canvas_course_site_ids=course['canvasSiteIds'],
                    course_label=course['label'],
                    instructors=(instructors + collaborators),
                    meeting=meeting,
                    publish_type=publish_type,
                    recording_type=recording_type,
                    room=room,
                    term_id=term_id,
                )

                if remove_blackout_conflicts:
                    remove_blackout_events(kaltura_schedule_id=kaltura_schedule_id)

                collaborator_uids = [collaborator['uid'] for collaborator in collaborators]

                scheduled = Scheduled.create(
                    course_display_name=course['label'],
                    instructor_uids=[instructor['uid'] for instructor in instructors],
                    collaborator_uids=collaborator_uids,
                    kaltura_schedule_id=kaltura_schedule_id,
                    meeting_days=meeting['days'],
                    meeting_end_date=get_recording_end_date(meeting),
                    meeting_end_time=meeting['endTime'],
                    meeting_start_date=get_recording_start_date(meeting, return_today_if_past_start=True),
                    meeting_start_time=meeting['startTime'],
                    publish_type_=publish_type,
                    recording_type_=recording_type,
                    room_id=room.id,
                    section_id=section_id,
                    term_id=term_id,
                )
                CoursePreference.update_collaborator_uids(
                    term_id=term_id,
                    section_id=section_id,
                    collaborator_uids=collaborator_uids,
                )

                if send_notifications:
                    notify_instructors_recordings_scheduled(
                        course=course,
                        scheduled=scheduled,
                        instructors=instructors,
                        collaborator_uids=collaborator_uids,
                    )
                all_scheduled.append(scheduled)
                app.logger.info(f'Recordings scheduled for course {section_id}')

            except Exception as e:
                # Exceptions generated by the Kaltura API client will include one of these codes:
                # https://developer.kaltura.com/api-docs/Error_Codes. Otherwise they're standard Python exceptions.
                summary = f"Failed to schedule recordings {course['label']} (section_id: {course['sectionId']})"
                app.logger.error(summary)
                app.logger.exception(e)
                send_system_error_email(
                    message=f'{summary}\n\n<pre>{traceback.format_exc()}</pre>',
                    subject=f'{summary[:50]}...' if len(summary) > 50 else summary,
                )

        else:
            app.logger.warn(f"""
                SKIP schedule recordings because room has no 'kaltura_resource_id'.
                Course: {course['label']}
                Room: {room.location}
            """)

    return all_scheduled


def _join(items, separator=', '):
    return separator.join(str(item) for item in items)
