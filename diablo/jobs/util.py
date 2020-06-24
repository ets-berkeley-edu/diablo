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
from itertools import islice

from diablo import db, std_commit
from diablo.externals.kaltura import Kaltura
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from diablo.merged.calnet import get_calnet_users_for_uids
from diablo.merged.emailer import send_system_error_email
from diablo.models.course_preference import CoursePreference
from diablo.models.cross_listing import CrossListing
from diablo.models.instructor import Instructor
from diablo.models.queued_email import notify_instructors_recordings_scheduled
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app
from KalturaClient.exceptions import KalturaClientException, KalturaException
from sqlalchemy import text


def insert_or_update_instructors(instructor_uids):
    instructors = []
    for instructor in get_calnet_users_for_uids(app=app, uids=instructor_uids).values():
        instructors.append({
            'dept_code': instructor.get('deptCode'),
            'email': instructor.get('campusEmail') or instructor.get('email'),
            'first_name': instructor.get('firstName') or '',
            'last_name': instructor.get('lastName') or '',
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

    kaltura_resource_ids_per_room = {}
    for resource in Kaltura().get_schedule_resources():
        room = Room.find_room(location=resource['name'])
        if room:
            kaltura_resource_ids_per_room[room.id] = resource['id']

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
                WHERE term_id = :term_id
                    AND meeting_days <> ''
                    AND meeting_end_date IS NOT NULL
                    AND meeting_end_time <> ''
                    AND meeting_location <> ''
                    AND meeting_start_date IS NOT NULL
                    AND meeting_start_time <> ''
                ORDER BY schedule, section_id
            """
    rows = db.session.execute(
        text(sql),
        {
            'term_id': term_id,
        },
    )
    cross_listings = {}
    previous_schedule = None
    primary_section_id = None

    for row in rows:
        section_id = row['section_id']
        schedule = row['schedule']
        if section_id not in cross_listings:
            if schedule != previous_schedule:
                primary_section_id = section_id
                cross_listings[primary_section_id] = []
            elif section_id not in cross_listings[primary_section_id]:
                cross_listings[primary_section_id].append(section_id)
        previous_schedule = schedule

    # Toss out section_ids with no cross-listings
    for section_id, section_ids in cross_listings.copy().items():
        if not section_ids:
            cross_listings.pop(section_id)

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

    std_commit()


def schedule_recordings(all_approvals, course):
    term_id = course['termId']
    section_id = int(course['sectionId'])
    all_approvals.sort(key=lambda a: a.created_at.isoformat())
    approval = all_approvals[-1]
    room = Room.get_room(approval.room_id)
    scheduled = None
    section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)

    def _send_error(e):
        error = f"Failed to schedule recordings {course['label']} (section_id: {course['sectionId']})"
        app.logger.error(error)
        app.logger.exception(e)
        send_system_error_email(message=str(e), subject=error)

    if room.kaltura_resource_id:
        meetings = course.get('meetings', {}).get('eligible', [])
        if len(meetings) != 1:
            _send_error(RuntimeError('Unique eligible meeting pattern not found for course'))
            return None
        meeting = meetings[0]
        try:
            kaltura_schedule_id = Kaltura().schedule_recording(
                canvas_course_site_ids=[c['courseSiteId'] for c in course['canvasCourseSites']],
                course_label=course['label'],
                instructors=course['instructors'],
                meeting=meeting,
                publish_type=approval.publish_type,
                recording_type=approval.recording_type,
                room=room,
                term_id=term_id,
            )
            scheduled = Scheduled.create(
                instructor_uids=[i['uid'] for i in course['instructors']],
                kaltura_schedule_id=kaltura_schedule_id,
                meeting_days=meeting['days'],
                meeting_end_date=get_recording_end_date(meeting),
                meeting_end_time=meeting['endTime'],
                meeting_start_date=get_recording_start_date(meeting),
                meeting_start_time=meeting['startTime'],
                publish_type_=approval.publish_type,
                recording_type_=approval.recording_type,
                room_id=room.id,
                section_id=section_id,
                term_id=term_id,
            )
            # Turn off opt-out setting if present.
            if section_id in section_ids_opted_out:
                CoursePreference.update_opt_out(
                    term_id=term_id,
                    section_id=section_id,
                    opt_out=False,
                )
            notify_instructors_recordings_scheduled(course=course, scheduled=scheduled)
            uids = [approval.approved_by_uid for approval in all_approvals]
            app.logger.info(f'Recordings scheduled for course {section_id} per approvals: {", ".join(uids)}')

        except (KalturaClientException, KalturaException) as e:
            # Error codes: https://developer.kaltura.com/api-docs/Error_Codes
            _send_error(e)

    else:
        app.logger.warn(f"""
            SKIP schedule recordings because room has no 'kaltura_resource_id'.
            Course: {course['label']}
            Room: {room.location}
            Latest approved_by_uid: {approval.approved_by_uid}
        """)

    return scheduled


def _join(items, separator=', '):
    return separator.join(str(item) for item in items)
