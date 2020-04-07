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
from diablo.lib.util import utc_now
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
    def get_sis_section(cls, term_id, section_id):
        sql = f"""
            SELECT * FROM sis_sections
            WHERE
                sis_term_id = :term_id
                AND sis_section_id = :section_id
                AND instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY sis_course_title, sis_section_id, instructor_uid
        """
        return db.session.execute(
            text(sql),
            {
                'section_id': section_id,
                'term_id': term_id,
            },
        )

    @classmethod
    def get_sis_sections(cls, term_id, instructor_uid):
        sql = f"""
            SELECT sis_section_id FROM sis_sections
            WHERE
                sis_term_id = :term_id
                AND instructor_uid = :instructor_uid
                AND instructor_role_code IN ('ICNT', 'PI', 'TNIC')
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
        return cls.get_sis_sections_per_id(term_id, section_ids)

    @classmethod
    def get_sis_sections_per_id(cls, term_id, section_ids):
        sql = """
            SELECT * FROM sis_sections
            WHERE
                sis_term_id = :term_id
                AND sis_section_id = ANY(:section_ids)
                AND instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            ORDER BY sis_course_title, sis_section_id, instructor_uid
        """
        return db.session.execute(
            text(sql),
            {
                'section_ids': section_ids,
                'term_id': term_id,
            },
        )

    @classmethod
    def get_sis_sections_per_location(cls, term_id, room_location):
        sql = f"""
            SELECT sis_section_id FROM sis_sections
            WHERE
                sis_term_id = :term_id
                AND meeting_location = :room_location
                AND instructor_role_code IN ('ICNT', 'PI', 'TNIC')
        """
        rows = db.session.execute(
            text(sql),
            {
                'room_location': room_location,
                'term_id': term_id,
            },
        )
        section_ids = []
        for row in rows:
            section_ids.append(row['sis_section_id'])
        return cls.get_sis_sections_per_id(term_id, section_ids)

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
