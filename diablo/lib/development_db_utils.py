"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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

from diablo import db, std_commit
from diablo.lib.util import utc_now
from diablo.models.sis_section import SisSection
from sqlalchemy import text


def save_mock_courses(json_file_path):
    courses = _load_mock_courses(json_file_path)
    if courses:
        for course in courses:
            section_id = course['section_id']
            if SisSection.get_course(term_id=course['term_id'], section_id=section_id):
                db.session.execute(text(f'DELETE FROM sis_sections WHERE section_id = {section_id}'))
        _save_courses(sis_sections=courses)
        std_commit(allow_test_environment=True)


def _load_mock_courses(json_file_path):
    with open(json_file_path, 'r') as file:
        json_ = json.loads(file.read())
        defaults = json_['defaults']
        instructors = json_['instructors']
        courses = []
        for c in json_['courses']:
            for key, value in defaults.items():
                if key not in c:
                    c[key] = value
            uid = c['instructor_uid']
            if uid:
                c['instructor_name'] = instructors[uid]
            else:
                c['instructor_name'] = None
                c['instructor_role_code'] = None
            courses.append(c)
        return courses


def _save_courses(sis_sections):
    now = utc_now().strftime('%Y-%m-%dT%H:%M:%S+00')
    query = """
        INSERT INTO sis_sections (
            allowed_units, course_name, course_title, created_at, deleted_at, instruction_format, instructor_name,
            instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date, meeting_end_time,
            meeting_location, meeting_start_date, meeting_start_time, section_id, section_num, term_id
        )
        SELECT
            allowed_units, course_name, course_title, created_at, deleted_at, instruction_format, instructor_name,
            instructor_role_code, instructor_uid, is_primary::BOOLEAN, meeting_days, meeting_end_date::TIMESTAMP,
            meeting_end_time, meeting_location, meeting_start_date::TIMESTAMP, meeting_start_time, section_id::INTEGER,
            section_num, term_id::INTEGER
        FROM json_populate_recordset(null::sis_sections, :json_dumps)
    """
    data = [
        {
            'allowed_units': row['allowed_units'],
            'course_name': row['course_name'],
            'course_title': row['course_title'],
            'created_at': now,
            'deleted_at': now if row.get('is_deleted') else None,
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
        } for row in sis_sections
    ]
    db.session.execute(query, {'json_dumps': json.dumps(data)})
