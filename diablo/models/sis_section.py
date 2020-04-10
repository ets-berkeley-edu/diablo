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
from diablo.lib.util import objects_to_dict_organized_by_section_id, utc_now
from diablo.models.approval import Approval
from diablo.models.canvas_course_site import CanvasCourseSite
from diablo.models.course_preference import CoursePreference
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from sqlalchemy import text


class SisSection(db.Model):
    __tablename__ = 'sis_sections'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    allowed_units = db.Column(db.String)
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
    sis_course_name = db.Column(db.String)
    sis_course_title = db.Column(db.Text)
    sis_instruction_format = db.Column(db.String)
    sis_section_id = db.Column(db.Integer, nullable=False)
    sis_section_num = db.Column(db.String)
    sis_term_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            sis_section_id,
            sis_term_id,
            allowed_units,
            instructor_role_code,
            instructor_name,
            instructor_uid,
            is_primary,
            meeting_days,
            meeting_end_date,
            meeting_end_time,
            meeting_location,
            meeting_start_date,
            meeting_start_time,
            sis_course_name,
            sis_course_title,
            sis_instruction_format,
            sis_section_num,
    ):
        self.sis_section_id = sis_section_id
        self.sis_term_id = sis_term_id
        self.allowed_units = allowed_units
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
        self.sis_course_name = sis_course_name
        self.sis_course_title = sis_course_title
        self.sis_instruction_format = sis_instruction_format
        self.sis_section_num = sis_section_num

    def __repr__(self):
        return f"""<SisSection
                    id={self.id}
                    sis_section_id={self.sis_section_id},
                    sis_term_id={self.sis_term_id},
                    allowed_units={self.allowed_units},
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
                    sis_course_name={self.sis_course_name},
                    sis_course_title={self.sis_course_title},
                    sis_instruction_format={self.sis_instruction_format},
                    sis_section_num={self.sis_section_num},
                    created_at={self.created_at}>
                """

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
    def get_courses_per_location(cls, term_id, location):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.sis_term_id = :term_id
                AND s.meeting_location = :location
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'location': location,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_invited(cls, term_id):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN sent_emails e ON e.section_id = s.sis_section_id
            WHERE
                s.sis_term_id = :term_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND e.template_type = 'invitation'
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN course_preferences c ON c.section_id = s.sis_section_id AND c.term_id = :term_id
            WHERE
                s.sis_term_id = :term_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND c.has_opted_out IS TRUE
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.sis_term_id = :term_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND r.capability IS NOT NULL
                AND NOT EXISTS (
                    SELECT FROM sent_emails
                    WHERE template_type = 'invitation' AND section_id = s.sis_section_id
                )
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_course(cls, term_id, section_id):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.sis_term_id = :term_id
                AND s.sis_section_id = :section_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
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
            JOIN approvals a ON a.section_id = s.sis_section_id
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN sent_emails e ON e.section_id = s.sis_section_id
            WHERE
                s.sis_term_id = :term_id
                AND r.id != a.room_id
                AND e.template_type = 'invitation'
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses(cls, term_id, section_ids):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.sis_term_id = :term_id
                AND s.sis_section_id = ANY(:section_ids)
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'section_ids': section_ids,
                'term_id': term_id,
            },
        )
        return _to_api_json(term_id=term_id, rows=rows)

    @classmethod
    def get_courses_partially_approved(cls, term_id):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN approvals a ON a.section_id = s.sis_section_id AND a.term_id = :term_id
            WHERE
                s.sis_term_id = :term_id
                AND NOT EXISTS (
                    SELECT FROM scheduled
                    WHERE section_id = s.sis_section_id
                )
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.sis_term_id = :term_id
                AND s.instructor_uid = :instructor_uid
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'instructor_uid': instructor_uid,
                'term_id': term_id,
            },
        )
        section_ids = []
        for row in rows:
            section_ids.append(row['sis_section_id'])
        return cls.get_courses(term_id, section_ids)

    @classmethod
    def get_courses_scheduled(cls, term_id):
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN scheduled d ON d.section_id = s.sis_section_id AND d.term_id = :term_id
            WHERE
                s.sis_term_id = :term_id
            ORDER BY s.sis_course_title, s.sis_section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        section_ids = []
        for row in rows:
            section_ids.append(row['sis_section_id'])
        return cls.get_courses(term_id, section_ids)

    @classmethod
    def refresh(cls, rows):
        cls.query.delete()
        now = utc_now().strftime('%Y-%m-%dT%H:%M:%S+00')
        count_per_chunk = 10000
        for chunk in range(0, len(rows), count_per_chunk):
            rows_subset = rows[chunk:chunk + count_per_chunk]
            query = """
                INSERT INTO sis_sections (
                    allowed_units, created_at, instructor_name, instructor_role_code, instructor_uid, is_primary, meeting_days,
                    meeting_end_date, meeting_end_time, meeting_location, meeting_start_date, meeting_start_time,
                    sis_course_name, sis_course_title, sis_instruction_format, sis_section_id, sis_section_num,
                    sis_term_id
                )
                SELECT
                    allowed_units, created_at, instructor_name, instructor_role_code, instructor_uid, is_primary, meeting_days,
                    meeting_end_date, meeting_end_time, meeting_location, meeting_start_date, meeting_start_time,
                    sis_course_name, sis_course_title, sis_instruction_format, sis_section_id, sis_section_num,
                    sis_term_id
                FROM json_populate_recordset(null::sis_sections, :json_dumps)
            """
            data = [
                {
                    'allowed_units': row['allowed_units'],
                    'created_at': now,
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
                    'sis_course_name': row['sis_course_name'],
                    'sis_course_title': row['sis_course_title'],
                    'sis_instruction_format': row['sis_instruction_format'],
                    'sis_section_id': int(row['sis_section_id']),
                    'sis_section_num': row['sis_section_num'],
                    'sis_term_id': int(row['sis_term_id']),
                } for row in rows_subset
            ]
            db.session.execute(query, {'json_dumps': json.dumps(data)})


def _to_api_json(term_id, rows):
    courses_per_id = {}
    section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)

    approvals = Approval.get_approvals_per_term(term_id)
    scheduled = Scheduled.get_all_scheduled(term_id)
    approvals_per_section_id = objects_to_dict_organized_by_section_id(objects=approvals)
    scheduled_per_section_id = objects_to_dict_organized_by_section_id(objects=scheduled)

    for row in rows:
        section_id = int(row['sis_section_id'])
        if section_id not in courses_per_id:
            has_opted_out = section_id in section_ids_opted_out
            approvals = [a.to_api_json() for a in approvals_per_section_id.get(section_id, [])]
            scheduled = [s.to_api_json() for s in scheduled_per_section_id.get(section_id, [])]
            course = {
                'allowedUnits': row['allowed_units'],
                'canvasCourseSites': _canvas_course_sites(term_id, section_id),
                'courseName': row['sis_course_name'], 'courseTitle': row['sis_course_title'],
                'hasOptedOut': has_opted_out, 'instructionFormat': row['sis_instruction_format'],
                'instructors': [], 'isPrimary': row['is_primary'],
                'meetingDays': _format_days(row['meeting_days']), 'meetingEndDate': row['meeting_end_date'],
                'meetingEndTime': _format_time(row['meeting_end_time']),
                'meetingLocation': row['meeting_location'], 'meetingStartDate': row['meeting_start_date'],
                'meetingStartTime': _format_time(row['meeting_start_time']), 'sectionId': section_id,
                'sectionNum': row['sis_section_num'], 'termId': row['sis_term_id'],
                'approvals': approvals,
                'scheduled': scheduled,
            }
            if scheduled:
                course['status'] = 'Scheduled'
            elif approvals:
                course['status'] = 'Partially Approved'
            else:
                invited = SentEmail.get_emails_of_type(
                    section_id=section_id,
                    template_type='invitation',
                    term_id=term_id,
                )
                course['status'] = 'Invited' if invited else 'Not Invited'

            room = Room.get_room(row['room_id']).to_api_json() if 'room_id' in row else None
            course['room'] = room
            for action in approvals + scheduled:
                room_id = action.pop('roomId')
                obsolete_action = not room or room['id'] != room_id
                action['room'] = Room.get_room(room_id).to_api_json() if obsolete_action else room
                action['isObsolete'] = obsolete_action
            courses_per_id[section_id] = course

        courses_per_id[section_id]['instructors'].append({
            'deptCode': row['instructor_dept_code'],
            'email': row['instructor_email'],
            'name': row['instructor_name'],
            'roleCode': row['instructor_role_code'],
            'uid': row['instructor_uid'],
        })
    return list(courses_per_id.values())


def _canvas_course_sites(term_id, section_id):
    canvas_course_sites = []
    for row in CanvasCourseSite.get_canvas_course_sites(term_id=term_id, section_id=section_id):
        canvas_course_sites.append({
            'courseSiteId': row.canvas_course_site_id,
            'courseSiteName': row.canvas_course_site_name,
        })
    return canvas_course_sites


def _format_days(days):
    n = 2
    return [(days[i:i + n]) for i in range(0, len(days), n)] if days else None


def _format_time(military_time):
    return datetime.strptime(military_time, '%H:%M').strftime('%I:%M %p').lower().lstrip(
        '0') if military_time else None
