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
from diablo.merged.calnet import get_calnet_users_for_uids
from diablo.models.cross_listing import CrossListing
from diablo.models.instructor import Instructor
from diablo.models.room import Room
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy import text


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


def refresh_cross_listings(term_id):
    # Populate 'cross_listings' table: If {123, 234, 345} is a set of cross-listed section_ids then:
    #  1. Section 123 will have a record in the 'sis_sections' table; 234 and 345 will not.
    #  2. The cross-listings table will get 123: [234, 345]
    #  3. We collapse the names of the three section into a single name/title for section 123

    # IMPORTANT: These will be ordered by schedule (time and location)
    sql = f"""
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
                    AND meeting_end_date <> ''
                    AND meeting_end_time <> ''
                    AND meeting_location <> ''
                    AND meeting_start_date <> ''
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
            else:
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

    delete_section_ids = []

    for cross_listings_chunk in chunks(cross_listings):
        cross_listing_count = len(cross_listings_chunk)
        query = 'INSERT INTO cross_listings (term_id, section_id, cross_listed_section_ids, created_at) VALUES'
        for index, (section_id, cross_listed_section_ids) in enumerate(cross_listings_chunk.items()):
            query += f' (:term_id, {section_id}, ' + "'{" + _join(cross_listed_section_ids, ', ') + "}', now())"
            if index < cross_listing_count - 1:
                query += ','
            # Cross-referenced section ids will be deleted in  sis_sections table
            delete_section_ids.extend(cross_listed_section_ids)
        db.session.execute(query, {'term_id': term_id})

    # Cross-listed section_ids are "deleted" in sis_sections, represented in cross_listings table
    SisSection.delete_all(section_ids=delete_section_ids, term_id=term_id)

    std_commit()


def _join(items, separator=', '):
    return separator.join(str(item) for item in items)
