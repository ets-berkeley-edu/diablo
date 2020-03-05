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

from diablo.externals.data_loch import get_section_denormalized, get_sections_denormalized
from diablo.externals.salesforce import get_capture_enabled_rooms


def get_section(term_id, section_id):
    rows = _normalize_rows(get_section_denormalized(term_id=term_id, section_id=section_id))
    return rows[0] if rows else None


def get_sections(term_id, instructor_uid):
    return _normalize_rows(get_sections_denormalized(term_id=term_id, instructor_uid=instructor_uid))


def _normalize_rows(rows):
    def _flatten_location(name):
        return name and ''.join(name.split()).lower()

    sections_per_id = {}
    instructor_uids_per_section_id = {}
    enabled_rooms = get_capture_enabled_rooms()

    enabled_locations = [_flatten_location(f'{r["building"]} {r["roomNumber"]}') for r in enabled_rooms]
    for row in rows:
        section_id = row['sis_section_id']
        if section_id not in sections_per_id:
            location = row['meeting_location']
            sections_per_id[section_id] = {
                'allowedUnits': row['allowed_units'],
                'courseName': row['sis_course_name'],
                'courseTitle': row['sis_course_title'],
                'instructionFormat': row['sis_instruction_format'],
                'instructorRoleCode': row['instructor_role_code'],
                'isEligibleForCourseCapture': _flatten_location(location) in enabled_locations,
                'isPrimary': row['is_primary'],
                'meetingDays': row['meeting_days'],
                'meetingEndDate': row['meeting_end_date'],
                'meetingEndTime': row['meeting_end_time'],
                'meetingLocation': location,
                'meetingStartDate': row['meeting_start_date'],
                'meetingStartTime': row['meeting_start_time'],
                'sectionId': section_id,
                'sectionNum': row['sis_section_num'],
                'termId': row['sis_term_id'],
            }
        if section_id not in instructor_uids_per_section_id:
            instructor_uids_per_section_id[section_id] = []
        instructor_uids_per_section_id[section_id].append(row['instructor_uid'])

    json_ = []
    for section_id, instructor_uids in instructor_uids_per_section_id.items():
        json_.append({
            **sections_per_id[section_id],
            **{
                'instructorUids': sorted(instructor_uids),
            },
        })
    return json_
