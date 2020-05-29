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
from datetime import datetime
import json

from diablo import db
from diablo.lib.util import format_days, format_time, utc_now
from diablo.models.approval import Approval
from diablo.models.canvas_course_site import CanvasCourseSite
from diablo.models.course_preference import CoursePreference
from diablo.models.cross_listing import CrossListing
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from sqlalchemy import text


class SisSection(db.Model):
    __tablename__ = 'sis_sections'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    allowed_units = db.Column(db.String)
    course_name = db.Column(db.String)
    course_title = db.Column(db.Text)
    instruction_format = db.Column(db.String)
    instructor_name = db.Column(db.Text)
    instructor_role_code = db.Column(db.String)
    instructor_uid = db.Column(db.String)
    is_primary = db.Column(db.Boolean)
    meeting_days = db.Column(db.String)
    meeting_end_date = db.Column(db.String)
    meeting_end_time = db.Column(db.String)
    meeting_location = db.Column(db.String)
    meeting_start_date = db.Column(db.String)
    meeting_start_time = db.Column(db.String)
    section_id = db.Column(db.Integer, nullable=False)
    section_num = db.Column(db.String)
    term_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    deleted_at = db.Column(db.DateTime)

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
    def delete_all(cls, section_ids, term_id):
        sql = 'UPDATE sis_sections SET deleted_at = now() WHERE term_id = :term_id AND section_id  = ANY(:section_ids)'
        db.session.execute(
            text(sql),
            {
                'section_ids': section_ids,
                'term_id': term_id,
            },
        )

    @classmethod
    def get_meeting_times(cls, term_id, section_id):
        course = cls.query.filter_by(term_id=term_id, section_id=section_id).first()
        if course:
            return course.meeting_days, course.meeting_start_time, course.meeting_end_time
        else:
            return None

    @classmethod
    def get_distinct_meeting_locations(cls):
        sql = """
            SELECT DISTINCT meeting_location FROM sis_sections
            WHERE
                meeting_location IS NOT NULL
                AND meeting_location != ''
                AND instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY meeting_location
        """
        return [row['meeting_location'] for row in db.session.execute(text(sql))]

    @classmethod
    def get_distinct_instructor_uids(cls):
        sql = 'SELECT DISTINCT instructor_uid FROM sis_sections WHERE instructor_uid IS NOT NULL'
        return [row['instructor_uid'] for row in db.session.execute(text(sql))]

    @classmethod
    def get_course(cls, term_id, section_id):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.term_id = :term_id
                AND s.is_primary IS TRUE
                AND s.section_id = :section_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND s.deleted_at IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'section_id': section_id,
                'term_id': term_id,
            },
        )
        api_json = _to_api_json(term_id=term_id, rows=rows)
        return api_json[0] if api_json else None

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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id AND d.deleted_at IS NULL
            WHERE
                s.term_id = :term_id
                AND s.is_primary IS TRUE
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND s.deleted_at IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        courses = []
        obsolete_instructor_uids = set()

        for course in _to_api_json(term_id=term_id, rows=rows):
            scheduled = course['scheduled']
            if scheduled['hasObsoleteRoom'] \
                    or scheduled['hasObsoleteInstructors'] \
                    or scheduled['hasObsoleteMeetingTimes']:
                courses.append(course)
            if scheduled['hasObsoleteInstructors']:
                obsolete_instructor_uids.update(scheduled['instructorUids'])
                scheduled['instructors'] = []

        if obsolete_instructor_uids:
            obsolete_instructors = {}
            instructor_query = 'SELECT uid, first_name, last_name from instructors where uid = any(:uids)'
            for row in db.session.execute(text(instructor_query), {'uids': list(obsolete_instructor_uids)}):
                obsolete_instructors[row['uid']] = {
                    'name': ' '.join([row['first_name'], row['last_name']]),
                    'uid': row['uid'],
                }
            for course in courses:
                if course['scheduled']['hasObsoleteInstructors']:
                    course['scheduled']['instructors'] = []
                    for uid in course['scheduled']['instructorUids']:
                        course['scheduled']['instructors'].append(obsolete_instructors.get(uid, {'name': '', 'uid': uid}))

        return courses

    @classmethod
    def get_courses(cls, term_id, section_ids=None):
        params = {'term_id': term_id}
        if section_ids is None:
            # If no section IDs are specified, return everything with an eligible room.
            course_filter = 'r.capability IS NOT NULL'
        else:
            course_filter = 's.section_id = ANY(:section_ids)'
            params['section_ids'] = section_ids
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
                AND {course_filter}
            JOIN instructors i ON i.uid = s.instructor_uid
                AND s.term_id = :term_id
                AND s.is_primary IS TRUE
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND s.deleted_at IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(text(sql), params)
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_invited(cls, term_id):
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
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id AND s.is_primary IS TRUE AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC') AND s.deleted_at IS NULL
            JOIN rooms r ON r.location = s.meeting_location AND r.capability IS NOT NULL
            JOIN sent_emails e ON e.section_id = s.section_id AND e.template_type = 'invitation'
            -- Omit approved courses, scheduled courses and opt-outs.
            LEFT JOIN approvals a ON a.section_id = s.section_id AND a.term_id = s.term_id AND a.deleted_at IS NULL
            LEFT JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = s.term_id AND d.deleted_at IS NULL
            LEFT JOIN course_preferences cp ON cp.section_id = s.section_id AND cp.term_id = s.term_id AND cp.has_opted_out IS TRUE
            WHERE a.section_id IS NULL AND d.section_id IS NULL and cp.section_id IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_eligible_courses_not_invited(cls, term_id):
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
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id AND s.is_primary IS TRUE AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC') AND s.deleted_at IS NULL
            JOIN rooms r ON r.location = s.meeting_location AND r.capability IS NOT NULL
            -- Omit sent invitations, approved courses, scheduled courses and opt-outs.
            LEFT JOIN approvals a ON a.section_id = s.section_id AND a.term_id = s.term_id AND a.deleted_at IS NULL
            LEFT JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = s.term_id AND d.deleted_at IS NULL
            LEFT JOIN sent_emails e on e.section_id = s.section_id AND e.term_id = s.term_id AND e.template_type = 'invitation'
            LEFT JOIN course_preferences cp ON cp.section_id = s.section_id AND cp.term_id = s.term_id AND cp.has_opted_out IS TRUE
            WHERE a.section_id IS NULL AND d.section_id IS NULL AND e.section_id IS NULL AND cp.section_id IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_opted_out(cls, term_id):
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
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND s.is_primary IS TRUE
                AND s.deleted_at IS NULL
            JOIN rooms r ON r.location = s.meeting_location AND r.capability IS NOT NULL
            JOIN course_preferences c ON c.section_id = s.section_id AND c.term_id = :term_id AND c.has_opted_out IS TRUE
            -- Omit scheduled courses.
            LEFT JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id AND d.deleted_at IS NULL
            WHERE d.section_id IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_partially_approved(cls, term_id):
        sql = """
            SELECT DISTINCT
                s.*,
                i.dept_code AS instructor_dept_code,
                i.email AS instructor_email,
                i.first_name || ' ' || i.last_name AS instructor_name,
                i.uid AS instructor_uid,
                r.id AS room_id,
                r.location AS room_location
            FROM sis_sections s
            JOIN approvals a
                ON s.term_id = :term_id AND s.is_primary IS TRUE AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC') AND s.deleted_at IS NULL
                AND a.section_id = s.section_id AND a.term_id = :term_id AND a.deleted_at IS NULL
            JOIN instructors i ON i.uid = s.instructor_uid
            -- This second course/instructor join is not for data display purposes, but to screen for the existence of any instructor who has
            -- not approved.
            JOIN sis_sections s2 ON s.term_id = s2.term_id AND s.section_id = s2.section_id
            JOIN instructors i2 ON
                i2.uid = s2.instructor_uid
                AND i2.uid NOT IN (
                    SELECT approved_by_uid
                    FROM approvals
                    WHERE section_id = s.section_id AND term_id = :term_id
                )
            JOIN rooms r ON r.location = s.meeting_location AND r.capability IS NOT NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_queued_for_scheduling(cls, term_id):
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
            JOIN approvals a
                ON s.term_id = :term_id AND s.is_primary IS TRUE AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC') AND s.deleted_at IS NULL
                AND a.section_id = s.section_id AND a.term_id = :term_id AND a.deleted_at IS NULL
                AND (
                    -- If approved by an admin, the course is considered queued.
                    s.section_id IN (
                        SELECT DISTINCT s.section_id
                        FROM sis_sections s
                        JOIN approvals a ON a.section_id = s.section_id AND a.term_id = :term_id AND s.term_id = :term_id AND a.deleted_at IS NULL
                        JOIN admin_users au ON a.approved_by_uid = au.uid
                    )
                    -- If not approved by an admin, we must screen out any courses with an instructor who has not approved.
                    OR s.section_id NOT IN (
                        SELECT DISTINCT s.section_id
                        FROM sis_sections s
                        LEFT JOIN approvals a
                            ON a.section_id = s.section_id AND a.term_id = :term_id AND a.approved_by_uid = s.instructor_uid AND a.deleted_at IS NULL
                        WHERE s.is_primary IS TRUE AND s.term_id = :term_id AND s.deleted_at IS NULL
                        AND a.section_id IS NULL
                    )
                )
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location AND r.capability IS NOT NULL
            -- Omit scheduled courses.
            LEFT JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id AND d.deleted_at IS NULL
            WHERE d.section_id IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_per_instructor_uid(cls, term_id, instructor_uid):
        # Find all section_ids, including deleted
        sql = """
            SELECT s.section_id, s.deleted_at
            FROM sis_sections s
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id
                AND s.is_primary IS TRUE
                AND s.instructor_uid = :instructor_uid
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
        """
        deleted_section_ids = []
        section_ids = []
        for row in db.session.execute(text(sql), {'instructor_uid': instructor_uid, 'term_id': term_id}):
            if row['deleted_at']:
                deleted_section_ids.append(row['section_id'])
            else:
                section_ids.append(row['section_id'])

        if deleted_section_ids:
            # Instructor is associated with cross-listed section_ids
            sql = f"""
                SELECT section_id
                FROM cross_listings
                WHERE
                    term_id = :term_id
                    AND cross_listed_section_ids && ARRAY[{','.join(str(id_) for id_ in deleted_section_ids)}]
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
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id
                AND s.is_primary IS TRUE
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND s.meeting_location = :location
                AND s.deleted_at IS NULL
            JOIN rooms r ON r.location = s.meeting_location
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'location': location,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows, include_rooms=False)

    @classmethod
    def get_courses_scheduled(cls, term_id):
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
            JOIN instructors i
                ON i.uid = s.instructor_uid
                AND s.term_id = :term_id
                AND s.is_primary IS TRUE
                AND s.deleted_at IS NULL
            JOIN rooms r ON r.location = s.meeting_location
            JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id AND d.deleted_at IS NULL
            ORDER BY s.course_name, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        section_ids = []
        for row in rows:
            section_ids.append(row['section_id'])
        return cls.get_courses(term_id, section_ids)

    @classmethod
    def get_random_co_taught_course(cls, term_id):
        sql = """
            SELECT section_id FROM (
                SELECT section_id, instructor_uid from sis_sections
                WHERE term_id = :term_id
                AND deleted_at IS NULL
                GROUP BY section_id, instructor_uid
            ) sections_by_instructor
            GROUP BY section_id
            HAVING COUNT(*) > 2
            LIMIT 1
        """
        section_id = db.session.execute(text(sql), {'term_id': term_id}).scalar()
        return cls.get_course(term_id, section_id)

    @classmethod
    def refresh(cls, sis_sections, term_id):
        db.session.execute(cls.__table__.delete().where(cls.term_id == term_id))
        now = utc_now().strftime('%Y-%m-%dT%H:%M:%S+00')
        count_per_chunk = 10000
        for chunk in range(0, len(sis_sections), count_per_chunk):
            rows_subset = sis_sections[chunk:chunk + count_per_chunk]
            query = """
                INSERT INTO sis_sections (
                    allowed_units, course_name, course_title, created_at, instruction_format, instructor_name,
                    instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date, meeting_end_time,
                    meeting_location, meeting_start_date, meeting_start_time, section_id, section_num, term_id
                )
                SELECT
                    allowed_units, course_name, course_title, created_at, instruction_format, instructor_name,
                    instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date, meeting_end_time,
                    meeting_location, meeting_start_date, meeting_start_time, section_id, section_num, term_id
                FROM json_populate_recordset(null::sis_sections, :json_dumps)
            """
            data = [
                {
                    'allowed_units': row['allowed_units'],
                    'course_name': row['course_name'],
                    'course_title': row['course_title'],
                    'created_at': now,
                    'instruction_format': row['instruction_format'],
                    'instructor_name': row['instructor_name'],
                    'instructor_role_code': row['instructor_role_code'],
                    'instructor_uid': row['instructor_uid'],
                    'is_primary': row['is_primary'],
                    'meeting_days': row['meeting_days'],
                    'meeting_end_date': row['meeting_end_date'],
                    'meeting_end_time': row['meeting_end_time'],
                    'meeting_location': row['meeting_location'],
                    'meeting_start_date': row['meeting_start_date'],
                    'meeting_start_time': row['meeting_start_time'],
                    'section_id': int(row['section_id']),
                    'section_num': row['section_num'],
                    'term_id': int(row['term_id']),
                } for row in rows_subset
            ]
            db.session.execute(query, {'json_dumps': json.dumps(data)})


def _to_api_json(term_id, rows, include_rooms=True):
    rows = rows.fetchall()
    section_ids = list(set(int(row['section_id']) for row in rows))
    courses_per_id = {}

    # Perform bulk queries and build data structures for feed generation.
    section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)

    invited_uids_by_section_id = {section_id: [] for section_id in section_ids}
    for invite in SentEmail.get_emails_of_type(section_ids=section_ids, template_type='invitation', term_id=term_id):
        for uid in list(filter(lambda u: u not in invited_uids_by_section_id[invite.section_id], invite.recipient_uids)):
            invited_uids_by_section_id[invite.section_id].append(uid)

    approvals_by_section_id = {section_id: [] for section_id in section_ids}
    for approval in Approval.get_approvals_per_section_ids(section_ids=section_ids, term_id=term_id):
        approvals_by_section_id[approval.section_id].append(approval.to_api_json())

    scheduled_results = Scheduled.get_scheduled_per_section_ids(section_ids=section_ids, term_id=term_id)
    scheduled_by_section_id = {s.section_id: s.to_api_json() for s in scheduled_results}

    cross_listings_per_section_id, instructors_per_section_id, canvas_sites_by_section_id = _get_cross_listed_courses(
        section_ids=section_ids,
        term_id=term_id,
        approvals=approvals_by_section_id,
        invited_uids=invited_uids_by_section_id,
    )

    rooms = Room.get_rooms(list(set(row['room_id'] for row in rows)))
    rooms_by_id = {room.id: room for room in rooms}

    # Construct course objects.
    # If course has multiple instructors then the section_id will be represented across multiple rows.
    for row in rows:
        section_id = int(row['section_id'])
        if section_id in courses_per_id:
            course = courses_per_id[section_id]
        else:
            # Approvals and scheduled (JSON)
            approvals = approvals_by_section_id.get(section_id)
            scheduled = scheduled_by_section_id.get(section_id)
            # Instructors per cross-listings
            cross_listed_courses = cross_listings_per_section_id.get(section_id, [])
            instructors = instructors_per_section_id.get(section_id, [])
            # Construct course
            course = {
                'allowedUnits': row['allowed_units'],
                'approvals': approvals,
                'canvasCourseSites': canvas_sites_by_section_id.get(section_id, []),
                'courseName': row['course_name'],
                'courseTitle': row['course_title'],
                'crossListings': cross_listed_courses,
                'deletedAt': format_time(row['deleted_at']),
                'hasOptedOut': section_id in section_ids_opted_out,
                'instructionFormat': row['instruction_format'],
                'instructors': instructors,
                'invitees': invited_uids_by_section_id.get(section_id),
                'isPrimary': row['is_primary'],
                'label': _construct_course_label(
                    course_name=row['course_name'],
                    instruction_format=row['instruction_format'],
                    section_num=row['section_num'],
                    cross_listings=cross_listed_courses,
                ),
                'meetingDays': format_days(row['meeting_days']),
                'meetingEndDate': row['meeting_end_date'],
                'meetingEndTime': format_time(row['meeting_end_time']),
                'meetingLocation': row['meeting_location'],
                'meetingStartDate': row['meeting_start_date'],
                'meetingStartTime': format_time(row['meeting_start_time']),
                'sectionId': section_id,
                'sectionNum': row['section_num'],
                'scheduled': scheduled,
                'termId': row['term_id'],
            }
            if scheduled:
                course['status'] = 'Scheduled'
            elif approvals:
                course['status'] = 'Approved'
            else:
                course['status'] = 'Invited' if course['invitees'] else 'Not Invited'

            if include_rooms:
                room = rooms_by_id.get(row['room_id']) if 'room_id' in row else None
                course['room'] = room.to_api_json() if room else None
            courses_per_id[section_id] = course

        # Note: Instructors associated with cross-listings are slurped up separately.
        instructor_uid = row['instructor_uid']
        if instructor_uid and instructor_uid not in [i['uid'] for i in course['instructors']]:
            course['instructors'].append(
                _to_instructor_json(
                    row=row,
                    approvals=course['approvals'],
                    invited_uids=course['invitees'],
                ),
            )

    # Next, construct the feed
    api_json = []
    for section_id, course in courses_per_id.items():
        _decorate_course(course)
        # Add course to the feed
        api_json.append(course)

    return api_json


def _decorate_course(course):
    room_id = course.get('room', {}).get('id')
    course['hasNecessaryApprovals'] = _has_necessary_approvals(course)
    if course['status'] == 'Approved' and not course['hasNecessaryApprovals']:
        course['status'] = 'Partially Approved'
    # Check for course changes w.r.t. room, meeting times, and instructors.
    if course['scheduled']:
        def _meeting(obj):
            return f'{obj["meetingDays"]}-{obj["meetingStartTime"]}-{obj["meetingEndTime"]}'

        instructor_uids = [i['uid'] for i in course['instructors']]
        has_obsolete_instructors = set(instructor_uids) != set(course.get('scheduled').get('instructorUids'))
        course['scheduled'].update({
            'hasObsoleteInstructors': has_obsolete_instructors,
            'hasObsoleteMeetingTimes': _meeting(course) != _meeting(course['scheduled']),
            'hasObsoleteRoom': room_id != course.get('scheduled').get('room', {}).get('id'),
        })

    for approval in course['approvals']:
        approval['hasObsoleteRoom'] = room_id != approval.get('room', {}).get('id')


def _get_cross_listed_courses(section_ids, term_id, approvals, invited_uids):
    # Return course and instructor info for cross-listings, and Canvas site info for cross-listings as well as the
    # principal section. Although cross-listed sections were "deleted" during SIS data refresh job, we still rely
    # on metadata from those deleted records.
    cross_listings_by_section_id = CrossListing.get_cross_listings_for_section_ids(section_ids=section_ids, term_id=term_id)
    all_cross_listing_ids = list(set(section_id for k, v in cross_listings_by_section_id.items() for section_id in v))
    all_section_ids = list(set(section_ids + all_cross_listing_ids))

    sql = """
        SELECT
            s.*,
            i.dept_code AS instructor_dept_code,
            i.email AS instructor_email,
            i.first_name || ' ' || i.last_name AS instructor_name,
            i.uid AS instructor_uid
        FROM sis_sections s
        JOIN instructors i ON i.uid = s.instructor_uid
        WHERE
            s.term_id = :term_id
            AND s.is_primary IS TRUE
            AND section_id = ANY(:all_cross_listing_ids)
        ORDER BY course_name, section_id
    """
    rows = db.session.execute(
        text(sql),
        {
            'all_cross_listing_ids': all_cross_listing_ids,
            'term_id': term_id,
        },
    )
    rows_by_cross_listing_id = {section_id: [] for section_id in all_cross_listing_ids}
    for row in rows:
        rows_by_cross_listing_id[row['section_id']].append(row)

    canvas_sites_by_cross_listing_id = {section_id: [] for section_id in all_section_ids}
    for site in CanvasCourseSite.get_canvas_course_sites(section_ids=all_section_ids, term_id=term_id):
        canvas_sites_by_cross_listing_id[site.section_id].append({
            'courseSiteId': site.canvas_course_site_id,
            'courseSiteName': site.canvas_course_site_name,
        })

    courses_by_section_id = {}
    instructors_by_section_id = {}
    canvas_sites_by_section_id = {}

    # First, collect Canvas sites associated with principal section ids.
    for section_id in section_ids:
        canvas_sites_by_section_id[section_id] = []
        for canvas_site in canvas_sites_by_cross_listing_id.get(section_id, []):
            canvas_sites_by_section_id[section_id].append(canvas_site)

    # Next, collect course data, instructor data, and Canvas sites associated with cross-listings.
    for section_id, cross_listing_ids in cross_listings_by_section_id.items():
        approvals_for_section = approvals.get(section_id, [])
        invited_uids_for_section = invited_uids.get(section_id, [])
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
                        instructors_by_section_id[section_id].append(
                            _to_instructor_json(row, approvals_for_section, invited_uids=invited_uids_for_section),
                        )
                for canvas_site in canvas_sites_by_cross_listing_id[cross_listing_id]:
                    canvas_sites_by_section_id[section_id].append(canvas_site)

    return courses_by_section_id, instructors_by_section_id, canvas_sites_by_section_id


def _to_instructor_json(row, approvals, invited_uids):
    instructor_uid = row['instructor_uid']
    return {
        'approval': next((a for a in approvals if a['approvedBy']['uid'] == instructor_uid), False),
        'deptCode': row['instructor_dept_code'],
        'email': row['instructor_email'],
        'name': row['instructor_name'],
        'roleCode': row['instructor_role_code'],
        'uid': instructor_uid,
        'wasSentInvite': instructor_uid in invited_uids,
    }


def _merge_distinct(label, other_labels):
    if label in other_labels:
        other_labels.remove(label)
    return [label] + list(set(other_labels))


def _construct_course_label(course_name, instruction_format, section_num, cross_listings):
    def _label(course_name_, instruction_format_, section_num_):
        return f'{course_name_}, {instruction_format_} {section_num_}'

    if cross_listings:
        distinct_instruction_format = set([instruction_format] + [c['instructionFormat'] for c in cross_listings])
        if len(cross_listings) > 1 or len(distinct_instruction_format) > 1:
            merged = _merge_distinct(
                _label(course_name, instruction_format, section_num),
                [_label(c['courseName'], c['instructionFormat'], c['sectionNum']) for c in cross_listings],
            )
            return ' | '.join(merged)
        else:
            distinct_course_names = _merge_distinct(course_name, [c['courseName'] for c in cross_listings])
            distinct_section_nums = _merge_distinct(section_num, [c['sectionNum'] for c in cross_listings])
            return f'{" | ".join(distinct_course_names)}, {instruction_format} {"/".join(distinct_section_nums)}'
    else:
        return _label(course_name, instruction_format, section_num)


def _has_necessary_approvals(course):
    if any(a['wasApprovedByAdmin'] for a in course['approvals']):
        return True
    elif course['instructors']:
        approval_uids = [a['approvedBy']['uid'] for a in course['approvals']]
        necessary_approval_uids = [i['uid'] for i in course['instructors']]
        return all(uid in approval_uids for uid in necessary_approval_uids)
    else:
        return False
