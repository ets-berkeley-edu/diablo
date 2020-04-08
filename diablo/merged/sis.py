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

from diablo import db
from diablo.models.canvas_course_site import CanvasCourseSite
from diablo.models.course_preference import CoursePreference
from diablo.models.sis_section import SisSection
from sqlalchemy import text


def get_course(term_id, section_id):
    section = SisSection.get_sis_section(term_id=term_id, section_id=section_id)
    if section:
        rows = _to_api_json(
            term_id=term_id,
            sis_sections=section,
        )
        return rows[0] if rows else None
    else:
        return None


def get_courses(term_id, section_ids):
    return _to_api_json(
        term_id=term_id,
        sis_sections=SisSection.get_sis_sections_per_id(
            term_id=term_id,
            section_ids=[section_id for section_id in section_ids],
        ),
    )


def get_courses_per_instructor(term_id, instructor_uid):
    return _to_api_json(
        term_id=term_id,
        sis_sections=SisSection.get_sis_sections(term_id=term_id, instructor_uid=instructor_uid),
    )


def get_courses_per_location(term_id, room_location):
    return _to_api_json(
        term_id=term_id,
        sis_sections=SisSection.get_sis_sections_per_location(term_id=term_id, room_location=room_location),
    )


def get_courses_invited(term_id):
    sql = f"""
        SELECT s.*, r.id AS room_id, r.location AS room_location FROM sis_sections s
        JOIN rooms r ON r.location = s.meeting_location
        JOIN sent_emails e ON e.section_id = s.sis_section_id
        WHERE
            s.sis_term_id = :term_id
            AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            AND e.template_type = 'invitation'
    """
    rows = db.session.execute(
        text(sql),
        {
            'term_id': term_id,
        },
    )
    return _to_api_json(term_id, rows)


def get_courses_opted_out(term_id):
    sql = f"""
        SELECT s.*, r.id AS room_id, r.location AS room_location FROM sis_sections s
        JOIN rooms r ON r.location = s.meeting_location
        JOIN course_preferences c ON c.section_id = s.section_id AND c.term_id = :term_id
        WHERE
            s.sis_term_id = :term_id
            AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            AND r.has_opted_out IS TRUE
    """
    rows = db.session.execute(
        text(sql),
        {
            'term_id': term_id,
        },
    )
    return _to_api_json(term_id, rows)


def get_eligible_courses_not_invited(term_id):
    sql = f"""
        SELECT s.*, r.id AS room_id, r.location AS room_location FROM sis_sections s
        JOIN rooms r ON r.location = s.meeting_location
        WHERE
            s.sis_term_id = :term_id
            AND s.instructor_role_code IN ('ICNT', 'PI', 'TNIC')
            AND r.capability IS NOT NULL
            AND NOT EXISTS (
                SELECT FROM sent_emails
                WHERE template_type = 'invitation' AND section_id = s.sis_section_id
            )
    """
    rows = db.session.execute(
        text(sql),
        {
            'term_id': term_id,
        },
    )
    return _to_api_json(term_id, rows)


def _to_api_json(term_id, sis_sections):
    sections_per_id = {}
    section_ids_opted_out = CoursePreference.get_section_ids_opted_out(term_id=term_id)
    for sis_section in sis_sections:
        section_id = int(sis_section['sis_section_id'])
        if section_id not in sections_per_id:
            room_id = sis_section['room_id'] if 'room_id' in sis_section else None
            sections_per_id[section_id] = {
                'allowedUnits': sis_section['allowed_units'],
                'canvasCourseSites': _canvas_course_sites(term_id, section_id),
                'courseName': sis_section['sis_course_name'],
                'courseTitle': sis_section['sis_course_title'],
                'hasOptedOut': section_id in section_ids_opted_out,
                'instructionFormat': sis_section['sis_instruction_format'],
                'instructors': [],
                'instructorName': sis_section['instructor_name'],
                'instructorRoleCode': sis_section['instructor_role_code'],
                'isPrimary': sis_section['is_primary'],
                'meetingDays': _format_days(sis_section['meeting_days']),
                'meetingEndDate': sis_section['meeting_end_date'],
                'meetingEndTime': _format_time(sis_section['meeting_end_time']),
                'meetingLocation': sis_section['meeting_location'],
                'meetingStartDate': sis_section['meeting_start_date'],
                'meetingStartTime': _format_time(sis_section['meeting_start_time']),
                'room': room_id and {
                    'id': room_id,
                    'location': sis_section['room_location'],
                },
                'sectionId': section_id,
                'sectionNum': sis_section['sis_section_num'],
                'termId': sis_section['sis_term_id'],
            }
        sections_per_id[section_id]['instructors'].append({
            'uid': sis_section['instructor_uid'],
            'name': sis_section['instructor_name'],
            'roleCode': sis_section['instructor_role_code'],
        })
    return list(sections_per_id.values())


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
    return datetime.strptime(military_time, '%H:%M').strftime('%I:%M %p').lower().lstrip('0') if military_time else None
