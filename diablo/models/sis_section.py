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
    def get_instructor_uids(cls, term_id, section_id):
        sql = """
            SELECT DISTINCT instructor_uid
            FROM sis_sections
            WHERE
                term_id = :term_id
                AND section_id = :section_id
                AND instructor_uid IS NOT NULL
        """
        rows = db.session.execute(
            text(sql),
            {
                'section_id': section_id,
                'term_id': term_id,
            },
        )
        return [row['instructor_uid'] for row in rows]

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
                s.term_id = :term_id
                AND s.meeting_location = :location
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
            JOIN sent_emails e ON e.section_id = s.section_id
            WHERE
                s.term_id = :term_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND e.template_type = 'invitation'
                AND r.capability IS NOT NULL
                AND NOT EXISTS (
                    SELECT FROM approvals
                    WHERE section_id = s.section_id AND term_id = s.term_id
                )
                AND NOT EXISTS (
                    SELECT FROM scheduled
                    WHERE section_id = s.section_id AND term_id = s.term_id
                )
                AND NOT EXISTS (
                    SELECT FROM course_preferences
                    WHERE section_id = s.section_id AND term_id = s.term_id AND has_opted_out IS TRUE
                )
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
            JOIN course_preferences c ON c.section_id = s.section_id AND c.term_id = :term_id
            WHERE
                s.term_id = :term_id
                AND c.has_opted_out IS TRUE
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND r.capability IS NOT NULL
                AND NOT EXISTS (
                    SELECT FROM scheduled
                    WHERE section_id = s.section_id AND term_id = s.term_id
                )
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
                s.term_id = :term_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
                AND r.capability IS NOT NULL
                AND NOT EXISTS (
                    SELECT FROM sent_emails
                    WHERE template_type = 'invitation' AND section_id = s.section_id
                )
                AND NOT EXISTS (
                    SELECT FROM approvals
                    WHERE section_id = s.section_id AND term_id = s.term_id
                )
                AND NOT EXISTS (
                    SELECT FROM scheduled
                    WHERE section_id = s.section_id AND term_id = s.term_id
                )
                AND NOT EXISTS (
                    SELECT FROM course_preferences
                    WHERE section_id = s.section_id AND term_id = s.term_id AND has_opted_out IS TRUE
                )
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
                s.term_id = :term_id
                AND s.section_id = :section_id
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN rooms r ON r.location = s.meeting_location
            JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id
            WHERE
                s.term_id = :term_id
            ORDER BY s.course_title, s.section_id, s.instructor_uid
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        courses = []
        for course in _to_api_json(term_id=term_id, rows=rows):
            scheduled = course['scheduled']
            if scheduled['hasObsoleteRoom'] \
                    or scheduled['hasObsoleteInstructors'] \
                    or scheduled['hasObsoleteMeetingTimes']:
                courses.append(course)
        return courses

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
                s.term_id = :term_id
                AND s.section_id = ANY(:section_ids)
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
            JOIN approvals a ON a.section_id = s.section_id AND a.term_id = :term_id
            JOIN instructors i ON i.uid = s.instructor_uid
            JOIN sent_emails e ON e.section_id = s.section_id
            JOIN rooms r ON r.location = s.meeting_location
            WHERE
                s.term_id = :term_id
                AND e.template_type = 'invitation'
                AND r.capability IS NOT NULL
                AND i.uid NOT IN (
                    SELECT approved_by_uid
                    FROM approvals
                    WHERE section_id = s.section_id AND term_id = :term_id
                )
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
                s.term_id = :term_id
                AND s.instructor_uid = :instructor_uid
                AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
            section_ids.append(row['section_id'])
        return cls.get_courses(term_id=term_id, section_ids=section_ids)

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
            JOIN scheduled d ON d.section_id = s.section_id AND d.term_id = :term_id
            WHERE
                s.term_id = :term_id
            ORDER BY s.course_title, s.section_id, s.instructor_uid
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
    courses_per_id = {}
    instructors_per_section_id = {}
    section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)
    # If course has multiple instructors then the section_id will be represented across multiple rows.
    for row in rows:
        approvals = []
        section_id = int(row['section_id'])
        if section_id not in courses_per_id:
            # Construct new course
            instructors_per_section_id[section_id] = []
            has_opted_out = section_id in section_ids_opted_out
            cross_listings = _get_cross_listed_courses(section_id=section_id, term_id=term_id)
            approvals, scheduled = _get_approvals_and_scheduled(
                section_ids=[section_id] + [c['sectionId'] for c in cross_listings],
                term_id=term_id,
            )
            course_name = row['course_name']
            instruction_format = row['instruction_format']
            section_num = row['section_num']
            course = {
                'allowedUnits': row['allowed_units'],
                'canvasCourseSites': _canvas_course_sites(term_id, section_id),
                'courseName': course_name,
                'courseTitle': row['course_title'],
                'crossListings': cross_listings,
                'hasOptedOut': has_opted_out,
                'instructionFormat': instruction_format,
                'instructors': [], 'isPrimary': row['is_primary'],
                'label': f'{course_name}, {instruction_format} {section_num}',
                'meetingDays': format_days(row['meeting_days']),
                'meetingEndDate': row['meeting_end_date'],
                'meetingEndTime': format_time(row['meeting_end_time']),
                'meetingLocation': row['meeting_location'],
                'meetingStartDate': row['meeting_start_date'],
                'meetingStartTime': format_time(row['meeting_start_time']),
                'sectionId': section_id,
                'sectionNum': section_num,
                'termId': row['term_id'],
                'approvals': approvals,
                'scheduled': scheduled,
            }
            invites = SentEmail.get_emails_of_type(
                section_id=section_id,
                template_type='invitation',
                term_id=term_id,
            )
            course['invitees'] = []
            for invite in invites:
                course['invitees'].extend(invite.recipient_uids)

            if scheduled:
                course['status'] = 'Scheduled'
            elif approvals:
                course['status'] = 'Partially Approved'
            else:
                course['status'] = 'Invited' if invites else 'Not Invited'

            if include_rooms:
                room = Room.get_room(row['room_id']).to_api_json() if 'room_id' in row else None
                course['room'] = room
            courses_per_id[section_id] = course

        # Build upon course object with one instructor per row.
        instructor_uid = row['instructor_uid']
        if instructor_uid not in [i['uid'] for i in instructors_per_section_id[section_id]]:
            instructors_per_section_id[section_id].append({
                'approval': next((a for a in approvals if a['approvedBy']['uid'] == instructor_uid), False),
                'deptCode': row['instructor_dept_code'],
                'email': row['instructor_email'],
                'name': row['instructor_name'],
                'roleCode': row['instructor_role_code'],
                'uid': instructor_uid,
                'wasSentInvite': instructor_uid in courses_per_id[section_id]['invitees'],
            })

    api_json = []
    for section_id, course in courses_per_id.items():
        room_id = course.get('room', {}).get('id')

        def _add_and_verify_room(approval_or_scheduled):
            action_room_id = approval_or_scheduled.get('room', {}).get('id')
            is_obsolete_room = not room_id or room_id != action_room_id
            approval_or_scheduled['hasObsoleteRoom'] = is_obsolete_room

        course['instructors'] = instructors_per_section_id[section_id]
        course['hasNecessaryApprovals'] = _has_necessary_approvals(course)
        scheduled = course['scheduled']
        # Check for course changes w.r.t. room, meeting times, and instructors.
        if scheduled:
            def _meeting(obj):
                return f'{obj["meetingDays"]}-{obj["meetingStartTime"]}-{obj["meetingEndTime"]}'

            instructor_uids = set([instructor['uid'] for instructor in course['instructors']])
            scheduled['hasObsoleteInstructors'] = instructor_uids != set(scheduled['instructorUids'])
            scheduled['hasObsoleteMeetingTimes'] = _meeting(course) != _meeting(scheduled)
            _add_and_verify_room(scheduled)

        for approval in course['approvals']:
            _add_and_verify_room(approval)

        # Add course to the feed
        api_json.append(course)
    return api_json


def _get_approvals_and_scheduled(section_ids, term_id):
    approvals = Approval.get_approvals_per_section_ids(section_ids=section_ids, term_id=term_id)
    scheduled = None
    for section_id in section_ids:
        if not scheduled:
            scheduled = Scheduled.get_scheduled(section_id=section_id, term_id=term_id)
            scheduled = scheduled and scheduled.to_api_json()
            break
    return [a.to_api_json() for a in approvals], scheduled


def _canvas_course_sites(term_id, section_id):
    canvas_course_sites = []
    for row in CanvasCourseSite.get_canvas_course_sites(term_id=term_id, section_id=section_id):
        canvas_course_sites.append({
            'courseSiteId': row.canvas_course_site_id,
            'courseSiteName': row.canvas_course_site_name,
        })
    return canvas_course_sites


def _get_cross_listed_courses(section_id, term_id):
    section_ids = CrossListing.get_cross_listed_sections(section_id=section_id, term_id=term_id)
    sql = f"""
        SELECT DISTINCT section_id, is_primary, course_name, course_title, instruction_format, section_num, term_id
        FROM sis_sections
        WHERE term_id = :term_id AND section_id = ANY(:section_ids)
        GROUP BY is_primary, section_id, course_name, course_title, instruction_format, section_num, term_id
        ORDER BY course_title, section_id
    """
    rows = db.session.execute(
        text(sql),
        {
            'section_ids': section_ids,
            'term_id': term_id,
        },
    )

    def _to_json(row):
        return {
            'courseTitle': row['course_title'],
            'isPrimary': row['is_primary'],
            'label': f"{row['course_name']}, {row['instruction_format']} {row['section_num']}",
            'sectionId': row['section_id'],
            'termId': row['term_id'],
        }
    return [_to_json(row) for row in rows]


def _has_necessary_approvals(course):
    if any(a['wasApprovedByAdmin'] for a in course['approvals']):
        return True
    else:
        approval_uids = [a['approvedBy']['uid'] for a in course['approvals']]
        necessary_approval_uids = [i['uid'] for i in course['instructors']]
        return all(uid in approval_uids for uid in necessary_approval_uids)
