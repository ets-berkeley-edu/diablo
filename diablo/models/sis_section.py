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
from datetime import datetime

from diablo import db
from diablo.externals.canvas import get_course_sites_by_id
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from diablo.lib.util import format_days, format_time, get_names_of_days, safe_strftime
from diablo.models.course_preference import CoursePreference
from diablo.models.cross_listing import CrossListing
from diablo.models.note import Note
from diablo.models.opt_out import OptOut
from diablo.models.room import Room
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.scheduled import Scheduled
from flask import current_app as app
from sqlalchemy import text

AUTHORIZED_INSTRUCTOR_ROLE_CODES = ['ICNT', 'PI', 'TNIC']
ALL_INSTRUCTOR_ROLE_CODES = ['APRX'] + AUTHORIZED_INSTRUCTOR_ROLE_CODES


class SisSection(db.Model):
    __tablename__ = 'sis_sections'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    allowed_units = db.Column(db.String)
    course_name = db.Column(db.String)
    course_title = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    deleted_at = db.Column(db.DateTime)
    instruction_format = db.Column(db.String)
    instructor_name = db.Column(db.Text)
    instructor_role_code = db.Column(db.String)
    instructor_uid = db.Column(db.String)
    is_primary = db.Column(db.Boolean)
    is_principal_listing = db.Column(db.Boolean, nullable=False, default=True)
    meeting_days = db.Column(db.String)
    meeting_end_date = db.Column(db.DateTime)
    meeting_end_time = db.Column(db.String)
    meeting_location = db.Column(db.String)
    meeting_start_date = db.Column(db.DateTime)
    meeting_start_time = db.Column(db.String)
    section_id = db.Column(db.Integer, nullable=False)
    section_num = db.Column(db.String)
    term_id = db.Column(db.Integer, nullable=False)

    def __init__(
            self,
            allowed_units,
            course_name,
            course_title,
            instruction_format,
            instructor_name,
            instructor_role_code,
            instructor_uid,
            is_primary,
            meeting_days,
            meeting_end_date,
            meeting_end_time,
            meeting_location,
            meeting_start_date,
            meeting_start_time,
            section_id,
            section_num,
            term_id,
    ):
        self.allowed_units = allowed_units
        self.course_name = course_name
        self.course_title = course_title
        self.instruction_format = instruction_format
        self.instructor_name = instructor_name
        self.instructor_role_code = instructor_role_code
        self.instructor_uid = instructor_uid
        self.is_primary = is_primary
        self.meeting_days = meeting_days
        self.meeting_end_date = meeting_end_date
        self.meeting_end_time = meeting_end_time
        self.meeting_location = meeting_location
        self.meeting_start_date = meeting_start_date
        self.meeting_start_time = meeting_start_time
        self.section_id = section_id
        self.section_num = section_num
        self.term_id = term_id

    def __repr__(self):
        return f"""<SisSection
                    id={self.id}
                    allowed_units={self.allowed_units},
                    course_name={self.course_name},
                    course_title={self.course_title},
                    instruction_format={self.instruction_format},
                    instructor_name={self.instructor_name},
                    instructor_role_code={self.instructor_role_code},
                    instructor_uid={self.instructor_uid},
                    is_primary={self.is_primary},
                    meeting_days={self.meeting_days},
                    meeting_end_date={self.meeting_end_date},
                    meeting_end_time={self.meeting_end_time},
                    meeting_location={self.meeting_location},
                    meeting_start_date={self.meeting_start_date},
                    meeting_start_time={self.meeting_start_time},
                    section_id={self.section_id},
                    section_num={self.section_num},
                    term_id={self.term_id},
                    created_at={self.created_at}>
                """

    @classmethod
    def set_non_principal_listings(cls, section_ids, term_id):
        sql = 'UPDATE sis_sections SET is_principal_listing = FALSE WHERE term_id = :term_id AND section_id  = ANY(:section_ids)'
        db.session.execute(
            text(sql),
            {
                'section_ids': section_ids,
                'term_id': term_id,
            },
        )

    @classmethod
    def get_distinct_meeting_locations(cls):
        sql = """
            SELECT DISTINCT meeting_location FROM sis_sections
            WHERE
                meeting_location IS NOT NULL
                AND meeting_location != ''
                AND instructor_role_code = ANY(:instructor_role_codes)
            ORDER BY meeting_location
        """
        args = {'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES}
        return [row['meeting_location'] for row in db.session.execute(text(sql), args)]

    @classmethod
    def get_distinct_instructor_uids(cls):
        sql = 'SELECT DISTINCT instructor_uid FROM sis_sections WHERE instructor_uid IS NOT NULL'
        return [row['instructor_uid'] for row in db.session.execute(text(sql))]

    @classmethod
    def get_course(
            cls,
            term_id,
            section_id,
            include_canvas_sites=False,
            include_deleted=False,
            include_notes=False,
            include_update_history=True,
    ):
        sql = f"""
            SELECT
                s.*,
                i.dept_code AS instructor_dept_code,
                i.email AS instructor_email,
                i.first_name || ' ' || i.last_name AS instructor_name,
                i.uid AS instructor_uid,
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            LEFT JOIN rooms r ON r.location = s.meeting_location
            LEFT JOIN instructors i
              ON i.uid = s.instructor_uid
              AND s.instructor_role_code = ANY(:instructor_role_codes)
            WHERE
                s.term_id = :term_id
                AND s.section_id = :section_id
                AND s.is_principal_listing IS TRUE
                {'' if include_deleted else ' AND s.deleted_at IS NULL '}
            ORDER BY s.course_name, s.section_id, s.instructor_uid, r.capability NULLS LAST
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
                'section_id': section_id,
                'term_id': term_id,
            },
        )
        api_json = _to_api_json(
            term_id=term_id,
            rows=rows,
            include_notes=include_notes,
            include_update_history=include_update_history,
        )
        feed = api_json[0] if api_json else None
        if feed and include_canvas_sites:
            feed['canvasSites'] = get_course_sites_by_id(feed['canvasSiteIds'])

        return feed

    @classmethod
    def get_course_changes(cls, term_id):
        sql = """
            SELECT
                s.*,
                i.dept_code AS instructor_dept_code,
                i.email AS instructor_email,
                i.first_name || ' ' || i.last_name AS instructor_name,
                i.uid AS instructor_uid,
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            LEFT JOIN rooms r ON r.location = s.meeting_location
            JOIN scheduled d ON
                d.section_id = s.section_id
                AND d.term_id = :term_id
                AND d.deleted_at IS NULL
            LEFT JOIN instructors i ON i.uid = s.instructor_uid
            WHERE
                s.term_id = :term_id
                AND (
                    s.deleted_at IS NOT NULL
                    OR (
                        (s.instructor_uid IS NULL OR s.instructor_role_code = ANY(:instructor_role_codes))
                        AND s.is_principal_listing IS TRUE
                    )
                )
            ORDER BY s.course_name, s.section_id, s.instructor_uid, r.capability NULLS LAST
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': ALL_INSTRUCTOR_ROLE_CODES,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows, include_administrative_proxies=True)

    @classmethod
    def get_courses(
            cls,
            term_id,
            exclude_scheduled=False,
            include_administrative_proxies=False,
            include_deleted=False,
            include_non_principal_sections=False,
            include_null_meeting_locations=False,
            section_ids=None,
    ):
        instructor_role_codes = ALL_INSTRUCTOR_ROLE_CODES if include_administrative_proxies else AUTHORIZED_INSTRUCTOR_ROLE_CODES
        params = {
            'instructor_role_codes': instructor_role_codes,
            'term_id': term_id,
        }
        if section_ids is None:
            # If no section IDs are specified, return any section with at least one eligible room.
            course_filter = f's.section_id IN ({_sections_with_at_least_one_eligible_room()})'
        else:
            course_filter = 's.section_id = ANY(:section_ids)'
            params['section_ids'] = section_ids
        if exclude_scheduled:
            exclude_scheduled_join = 'LEFT JOIN scheduled sch ON sch.term_id = s.term_id AND sch.section_id = s.section_id AND sch.deleted_at IS NULL'
        else:
            exclude_scheduled_join = ''

        sql = f"""
            SELECT
                s.*,
                i.dept_code AS instructor_dept_code,
                i.email AS instructor_email,
                i.first_name || ' ' || i.last_name AS instructor_name,
                i.uid AS instructor_uid,
                {'sch.kaltura_schedule_id,' if exclude_scheduled else ''}
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            {'LEFT' if include_null_meeting_locations else ''} JOIN rooms r ON r.location = s.meeting_location
            LEFT JOIN instructors i ON i.uid = s.instructor_uid
            {exclude_scheduled_join}
            WHERE
                {course_filter}
                AND s.term_id = :term_id
                AND (s.instructor_uid IS NULL OR s.instructor_role_code = ANY(:instructor_role_codes))
                {'' if include_non_principal_sections else 'AND s.is_principal_listing IS TRUE'}
                {'' if include_deleted else ' AND s.deleted_at IS NULL '}
                {'AND sch.kaltura_schedule_id IS NULL' if exclude_scheduled else ''}
            ORDER BY s.course_name, s.section_id, s.instructor_uid, r.capability NULLS LAST
        """
        rows = db.session.execute(text(sql), params)
        return _to_api_json(term_id=term_id, rows=rows, include_administrative_proxies=include_administrative_proxies)

    @classmethod
    def get_courses_opted_out(cls, term_id):
        sql = f"""
            SELECT
                s.*,
                i.dept_code AS instructor_dept_code,
                i.email AS instructor_email,
                i.first_name || ' ' || i.last_name AS instructor_name,
                i.uid AS instructor_uid,
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            JOIN rooms r ON r.location = s.meeting_location
            JOIN opt_outs o ON
                o.instructor_uid = s.instructor_uid AND
                (o.section_id = s.section_id OR o.section_id IS NULL) AND
                (o.term_id = :term_id OR o.term_id IS NULL)
            LEFT JOIN instructors i ON i.uid = s.instructor_uid
            WHERE
                s.term_id = :term_id
                AND (s.instructor_uid IS NULL OR s.instructor_role_code = ANY(:instructor_role_codes))
                AND s.is_principal_listing IS TRUE
                AND s.section_id IN ({_sections_with_at_least_one_eligible_room()})
                AND s.deleted_at IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid, r.capability NULLS LAST
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_per_instructor_uid(cls, term_id, instructor_uid):
        # Find all section_ids, including cross-listings
        sql = """
            SELECT s.section_id, s.is_principal_listing
            FROM sis_sections s
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id
                AND s.instructor_uid = :instructor_uid
                AND s.instructor_role_code = ANY(:instructor_role_codes)
            WHERE s.deleted_at IS NULL
        """
        non_principal_section_ids = []
        section_ids = []
        args = {
            'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
            'instructor_uid': instructor_uid,
            'term_id': term_id,
        }
        for row in db.session.execute(text(sql), args):
            if row['is_principal_listing'] is False:
                non_principal_section_ids.append(row['section_id'])
            else:
                section_ids.append(row['section_id'])

        if non_principal_section_ids:
            # Instructor is associated with cross-listed section_ids
            sql = f"""
                SELECT section_id
                FROM cross_listings
                WHERE
                    term_id = :term_id
                    AND cross_listed_section_ids && ARRAY[{','.join(str(id_) for id_ in non_principal_section_ids)}]
            """
            for row in db.session.execute(text(sql), {'section_ids': instructor_uid, 'term_id': term_id}):
                section_ids.append(row['section_id'])

        return cls.get_courses(term_id=term_id, section_ids=section_ids)

    @classmethod
    def get_courses_per_location(cls, term_id, location):
        sql = """
            SELECT
                s.*,
                i.dept_code AS instructor_dept_code,
                i.email AS instructor_email,
                i.first_name || ' ' || i.last_name AS instructor_name,
                i.uid AS instructor_uid,
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            JOIN rooms r ON r.location = s.meeting_location
            LEFT JOIN instructors i ON i.uid = s.instructor_uid
            WHERE
                s.term_id = :term_id
                AND (s.instructor_uid IS NULL OR s.instructor_role_code = ANY(:instructor_role_codes))
                AND s.is_principal_listing IS TRUE
                AND s.meeting_location = :location
                AND s.deleted_at IS NULL
            ORDER BY CASE LEFT(s.meeting_days, 2)
              WHEN 'MO' THEN 1
              WHEN 'TU' THEN 2
              WHEN 'WE' THEN 3
              WHEN 'TH' THEN 4
              WHEN 'FR' THEN 5
              WHEN 'SA' THEN 6
              WHEN 'SU' THEN 7
              ELSE 8
            END,
            s.meeting_start_time, s.section_id
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
                'location': location,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows, include_rooms=False)

    @classmethod
    def get_courses_scheduled(cls, term_id):
        scheduled_section_ids = list(cls._section_ids_scheduled(term_id))
        return cls.get_courses(
            include_deleted=True,
            section_ids=scheduled_section_ids,
            term_id=term_id,
        )

    @classmethod
    def get_courses_without_instructors(cls, term_id):
        sql = f"""
            SELECT
                s.*,
                NULL AS instructor_dept_code,
                NULL AS instructor_email,
                NULL AS instructor_name,
                NULL AS instructor_uid,
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.term_id = :term_id
                AND s.instructor_uid IS NULL
                AND s.is_principal_listing IS TRUE
                AND s.section_id IN ({_sections_with_at_least_one_eligible_room()})
                AND s.deleted_at IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid, r.capability NULLS LAST
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_random_co_taught_course(cls, term_id):
        def _get_section_id(in_eligible_room=True):
            sql = f"""
                SELECT section_id FROM (
                    SELECT s.section_id, s.instructor_uid
                    FROM sis_sections s
                    {'JOIN rooms r ON r.location = s.meeting_location' if in_eligible_room else ''}
                    WHERE
                        s.term_id = :term_id
                        AND s.deleted_at IS NULL
                    AND s.is_principal_listing IS TRUE
                    {'AND r.capability IS NOT NULL' if in_eligible_room else ''}
                    GROUP BY s.section_id, s.instructor_uid
                ) sections_by_instructor
                GROUP BY section_id
                HAVING COUNT(*) > 2
                LIMIT 1
            """
            return db.session.execute(text(sql), {'term_id': term_id}).scalar()
        section_id = _get_section_id() or _get_section_id(in_eligible_room=False)
        return cls.get_course(section_id=section_id, term_id=term_id)

    @classmethod
    def is_teaching(cls, term_id, uid):
        sql = """
            SELECT id
            FROM sis_sections
            WHERE term_id = :term_id
                AND instructor_uid = :uid
                AND instructor_role_code = ANY(:instructor_role_codes)
                AND deleted_at IS NULL
            LIMIT 1
        """
        results = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
                'term_id': term_id,
                'uid': uid,
            },
        )
        return results.rowcount > 0

    @classmethod
    def _section_ids_scheduled(cls, term_id):
        sql = """
            SELECT DISTINCT s.section_id
            FROM sis_sections s
            JOIN rooms r ON r.location = s.meeting_location
            JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id AND d.deleted_at IS NULL
            LEFT JOIN instructors i ON i.uid = s.instructor_uid
            WHERE
                s.term_id = :term_id
                AND (s.instructor_uid IS NULL OR s.instructor_role_code = ANY(:instructor_role_codes))
                AND s.is_principal_listing IS TRUE
            ORDER BY s.section_id
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_role_codes': AUTHORIZED_INSTRUCTOR_ROLE_CODES,
                'term_id': term_id,
            },
        )
        return set([row['section_id'] for row in rows])


def _to_api_json(term_id, rows, include_administrative_proxies=False, include_notes=False, include_rooms=True, include_update_history=False):  # noqa C901
    rows = rows.fetchall()
    section_ids = list(set(int(row['section_id']) for row in rows))
    courses_per_id = {}

    # Perform bulk queries and build data structures for feed generation.
    all_course_preferences = CoursePreference.get_all_course_preferences(term_id=term_id)
    course_preferences_by_section_id = dict((p.section_id, p) for p in all_course_preferences)

    opt_outs_by_section_id = {}
    blanket_opt_outs_by_instructor_uid = {}
    for o in OptOut.get_all_opt_outs(term_id=term_id):
        if o.section_id:
            if o.section_id not in opt_outs_by_section_id:
                opt_outs_by_section_id[o.section_id] = []
            opt_outs_by_section_id[o.section_id].append(o)
        else:
            if o.instructor_uid not in blanket_opt_outs_by_instructor_uid:
                blanket_opt_outs_by_instructor_uid[o.instructor_uid] = []
            blanket_opt_outs_by_instructor_uid[o.instructor_uid].append(o)

    scheduled_results = Scheduled.get_scheduled_per_section_ids(section_ids=section_ids, term_id=term_id)

    room_ids = set(row['room_id'] for row in rows)
    room_ids.update(s.room_id for s in scheduled_results)
    rooms = Room.get_rooms(list(room_ids))
    rooms_by_id = {room.id: room for room in rooms}

    scheduled_by_section_id = {}
    for s in scheduled_results:
        if s.section_id not in scheduled_by_section_id:
            scheduled_by_section_id[s.section_id] = []
        scheduled_by_section_id[s.section_id].append(s.to_api_json(rooms_by_id=rooms_by_id))

    if include_notes:
        note_results = Note.get_notes_for_section_ids(section_ids=section_ids, term_id=term_id)
        notes_by_section_id = {note.section_id: note.body for note in note_results}

    cross_listings_per_section_id, instructors_per_section_id = _get_cross_listed_courses(
        include_administrative_proxies=include_administrative_proxies,
        section_ids=section_ids,
        term_id=term_id,
    )

    # Construct course objects.
    # If course has multiple instructors or multiple rooms then the section_id will be represented across multiple rows.
    # Multiple rooms are rare, but a course is sometimes associated with both an eligible and an ineligible room. We
    # order rooms in SQL by capability, NULLS LAST, and use scheduling data from the first row available.
    for row in rows:
        section_id = int(row['section_id'])
        if section_id in courses_per_id:
            course = courses_per_id[section_id]
        else:
            # Instructors per cross-listings
            cross_listed_courses = cross_listings_per_section_id.get(section_id, [])
            instructors = instructors_per_section_id.get(section_id, [])

            cross_listed_section_ids = [c['sectionId'] for c in cross_listed_courses]
            cross_listed_section_ids.append(section_id)
            schedule_updates = ScheduleUpdate.get_update_history_for_section_ids(term_id=row['term_id'], section_ids=cross_listed_section_ids)

            # Construct course
            scheduled = scheduled_by_section_id.get(section_id)
            opt_outs = opt_outs_by_section_id.get(section_id) or []

            preferences = course_preferences_by_section_id.get(section_id)
            if preferences:
                preferences = preferences.to_api_json()
            elif scheduled:
                preferences = scheduled[0]
            else:
                preferences = {}

            if preferences.get('canvasSiteIds'):
                canvas_site_ids = [int(site_id) for site_id in preferences['canvasSiteIds']]
            else:
                canvas_site_ids = None

            course = {
                'allowedUnits': row['allowed_units'],
                'collaborators': preferences.get('collaborators'),
                'collaboratorUids': preferences.get('collaboratorUids'),
                'canvasSiteIds': canvas_site_ids,
                'courseName': row['course_name'],
                'courseTitle': row['course_title'],
                'crossListings': cross_listed_courses,
                'deletedAt': safe_strftime(row['deleted_at'], '%Y-%m-%d'),
                'hasBlanketOptedOut': False,
                'hasOptedOut': True if len(opt_outs) else False,
                'instructionFormat': row['instruction_format'],
                'instructors': instructors,
                'isPrimary': row['is_primary'],
                'label': _construct_course_label(
                    course_name=row['course_name'],
                    instruction_format=row['instruction_format'],
                    section_num=row['section_num'],
                    cross_listings=cross_listed_courses,
                ),
                'meetings': {
                    'eligible': [],
                    'ineligible': [],
                },
                'nonstandardMeetingDates': False,
                'optOuts': [o.to_api_json() for o in opt_outs],
                'publishType': preferences.get('publishType'),
                'publishTypeName': preferences.get('publishTypeName'),
                'recordingType': preferences.get('recordingType'),
                'recordingTypeName': preferences.get('recordingTypeName'),
                'sectionId': section_id,
                'sectionNum': row['section_num'],
                'scheduled': scheduled,
                'termId': row['term_id'],
                'updateHistory': [u.to_api_json() for u in schedule_updates],
            }
            courses_per_id[section_id] = course

        # Note: Instructors associated with cross-listings are slurped up separately.
        instructor_uid = row['instructor_uid']
        instructor_uid = instructor_uid.strip() if instructor_uid else None
        if instructor_uid and instructor_uid not in [i['uid'] for i in course['instructors']]:
            instructor_json = _to_instructor_json(row)
            # Note:
            # 1. If the course IS NOT DELETED then include only non-deleted instructors.
            # 2. If the course IS DELETED then include deleted instructors.
            if not instructor_json['deletedAt'] or course['deletedAt']:
                course['instructors'].append(instructor_json)

        blanket_opt_outs = []
        decorated_course_instructors = []
        for i in course['instructors']:
            instructor_has_opted_out = False
            blanket_opt_outs_for_instructor = blanket_opt_outs_by_instructor_uid.get(i['uid'])
            if blanket_opt_outs_for_instructor:
                instructor_has_opted_out = True
                blanket_opt_outs += blanket_opt_outs_for_instructor
            elif next((o for o in opt_outs if o.instructor_uid == i['uid']), None):
                instructor_has_opted_out = True
            decorated_course_instructors.append({**i, **{'hasOptedOut': instructor_has_opted_out}})
        course['instructors'] = decorated_course_instructors
        if blanket_opt_outs:
            course['hasBlanketOptedOut'] = True
            course['hasOptedOut'] = True
            course['optOuts'] += [o.to_api_json() for o in blanket_opt_outs]

        meeting = _to_meeting_json(row)
        eligible_meetings = course['meetings']['eligible']
        ineligible_meetings = course['meetings']['ineligible']
        if not next((m for m in (eligible_meetings + ineligible_meetings) if meeting.items() <= m.items()), None):
            room = rooms_by_id.get(row['room_id']) if 'room_id' in row.keys() else None
            if room and room.capability:
                meeting['eligible'] = True
                meeting.update({
                    'recordingEndDate': safe_strftime(get_recording_end_date(meeting), '%Y-%m-%d'),
                    'recordingStartDate': safe_strftime(get_recording_start_date(meeting), '%Y-%m-%d'),
                })
                eligible_meetings.append(meeting)
                eligible_meetings.sort(key=lambda m: f"{m['startDate']} {m['startTime']}")
                if meeting['startDate'] != app.config['CURRENT_TERM_BEGIN'] or meeting['endDate'] != app.config['CURRENT_TERM_END']:
                    course['nonstandardMeetingDates'] = True
            else:
                meeting['eligible'] = False
                ineligible_meetings.append(meeting)
                ineligible_meetings.sort(key=lambda m: f"{m['startDate']} {m['startTime']}")
            if include_rooms:
                meeting['room'] = room.to_api_json() if room else None

        if include_notes and section_id in notes_by_section_id:
            course['note'] = notes_by_section_id[section_id]

    # Next, construct the feed
    api_json = []
    for section_id, course in courses_per_id.items():
        _decorate_course_meeting_type(course)
        # Add course to the feed
        api_json.append(course)

    return api_json


def _decorate_course_meeting_type(course):
    # 'meetingType' is our own homegrown typology. See DIABLO-436.
    if len(course['meetings']['eligible']) > 1:
        course['meetingType'] = 'D'
    elif course['nonstandardMeetingDates']:
        course['meetingType'] = 'C'
    elif len(course['meetings']['eligible'] + course['meetings']['ineligible']) > 1:
        course['meetingType'] = 'B'
    else:
        course['meetingType'] = 'A'


def _get_cross_listed_courses(section_ids, term_id, include_administrative_proxies=False):
    # Return course and instructor info for cross-listings as well as the
    # principal section. Although cross-listed sections were "deleted" during SIS data refresh job, we still rely
    # on metadata from those deleted records.
    cross_listings_by_section_id = CrossListing.get_cross_listings_for_section_ids(section_ids=section_ids, term_id=term_id)
    all_cross_listing_ids = list(set(section_id for k, v in cross_listings_by_section_id.items() for section_id in v))

    sql = """
        SELECT
            s.*,
            i.dept_code AS instructor_dept_code,
            i.email AS instructor_email,
            i.first_name || ' ' || i.last_name AS instructor_name,
            i.uid AS instructor_uid
        FROM sis_sections s
        LEFT JOIN instructors i ON i.uid = s.instructor_uid
        WHERE
            s.term_id = :term_id
            AND s.section_id = ANY(:all_cross_listing_ids)
            AND s.instructor_role_code = ANY(:instructor_role_codes)
            AND s.deleted_at IS NULL
        ORDER BY course_name, section_id
    """
    rows = db.session.execute(
        text(sql),
        {
            'all_cross_listing_ids': all_cross_listing_ids,
            'instructor_role_codes': ALL_INSTRUCTOR_ROLE_CODES if include_administrative_proxies else AUTHORIZED_INSTRUCTOR_ROLE_CODES,
            'term_id': term_id,
        },
    )
    rows_by_cross_listing_id = {section_id: [] for section_id in all_cross_listing_ids}
    for row in rows:
        rows_by_cross_listing_id[row['section_id']].append(row)

    courses_by_section_id = {}
    instructors_by_section_id = {}

    # Collect course and instructor data associated with cross-listings.
    for section_id, cross_listing_ids in cross_listings_by_section_id.items():
        courses_by_section_id[section_id] = []
        instructors_by_section_id[section_id] = []
        for cross_listing_id in cross_listing_ids:
            if rows_by_cross_listing_id[cross_listing_id]:
                # Our first row provides course-specific data.
                row = rows_by_cross_listing_id[cross_listing_id][0]
                courses_by_section_id[section_id].append({
                    'courseName': row['course_name'],
                    'courseTitle': row['course_title'],
                    'instructionFormat': row['instruction_format'],
                    'sectionNum': row['section_num'],
                    'isPrimary': row['is_primary'],
                    'label': f"{row['course_name']}, {row['instruction_format']} {row['section_num']}",
                    'sectionId': row['section_id'],
                    'termId': row['term_id'],
                })
                # Instructor-specific data may be spread across multiple rows.
                for row in rows_by_cross_listing_id[cross_listing_id]:
                    if row['instructor_uid'] and row['instructor_uid'] not in [i['uid'] for i in instructors_by_section_id[section_id]]:
                        instructor_json = _to_instructor_json(row)
                        uid = (instructor_json['uid'] or '').strip() if instructor_json else None
                        if uid and not instructor_json['deletedAt']:
                            instructors_by_section_id[section_id].append(instructor_json)
    return courses_by_section_id, instructors_by_section_id


def _sections_with_at_least_one_eligible_room():
    return """
        SELECT DISTINCT s2.section_id
        FROM sis_sections s2 JOIN rooms r2
            ON r2.location = s2.meeting_location
            AND r2.capability IS NOT NULL
            AND s2.term_id = :term_id
            AND (s2.instructor_uid IS NULL OR s2.instructor_role_code = ANY(:instructor_role_codes))
            AND s2.is_principal_listing IS TRUE
            AND s2.deleted_at IS NULL
    """


def _to_instructor_json(row):
    instructor_uid = row['instructor_uid']
    instructor_json = {
        'deletedAt': safe_strftime(row['deleted_at'], '%Y-%m-%d'),
        'deptCode': row['instructor_dept_code'],
        'email': row['instructor_email'],
        'name': row['instructor_name'],
        'roleCode': row['instructor_role_code'],
        'uid': instructor_uid,
    }
    return instructor_json


def _to_meeting_json(row):
    end_date = row['meeting_end_date']
    start_date = row['meeting_start_date']
    formatted_days = format_days(row['meeting_days'])
    return {
        'days': row['meeting_days'],
        'daysFormatted': formatted_days,
        'daysNames': get_names_of_days(formatted_days),
        'endDate': safe_strftime(end_date, '%Y-%m-%d'),
        'endTime': row['meeting_end_time'],
        'endTimeFormatted': format_time(row['meeting_end_time']),
        'location': row['meeting_location'],
        'startDate': safe_strftime(start_date, '%Y-%m-%d'),
        'startTime': row['meeting_start_time'],
        'startTimeFormatted': format_time(row['meeting_start_time']),
    }


def _merge_distinct(label, other_labels):
    if label in other_labels:
        other_labels.remove(label)
    return [label] + list(set(other_labels))


def _construct_course_label(course_name, instruction_format, section_num, cross_listings):
    def _label(course_name_, instruction_format_, section_num_):
        return f'{course_name_}, {instruction_format_} {section_num_}'

    if cross_listings:
        merged = _merge_distinct(
            _label(course_name, instruction_format, section_num),
            [_label(c['courseName'], c['instructionFormat'], c['sectionNum']) for c in cross_listings],
        )
        return ' | '.join(merged)
    else:
        return _label(course_name, instruction_format, section_num)
