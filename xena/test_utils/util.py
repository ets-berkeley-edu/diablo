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

from datetime import datetime, timedelta
import json

import dateutil.parser
from diablo import db, std_commit
from flask import current_app as app
from sqlalchemy import text
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.room import Room
from xena.models.section import Section


def get_xena_browser():
    return app.config['XENA_BROWSER']


def get_click_sleep():
    return app.config['CLICK_SLEEP']


def get_short_timeout():
    return app.config['TIMEOUT_SHORT']


def get_medium_timeout():
    return app.config['TIMEOUT_MEDIUM']


def get_long_timeout():
    return app.config['TIMEOUT_LONG']


def default_download_dir():
    return f'{app.config["BASE_DIR"]}/xena/downloads'


def get_admin_uid():
    return app.config['ADMIN_UID']


def get_kaltura_username():
    return app.config['KALTURA_USERNAME']


def get_kaltura_password():
    return app.config['KALTURA_PASSWORD']


def get_kaltura_term_date_str(date):
    return datetime.strftime(date, '%m/%d/%Y')


def parse_rooms_data():
    with open(app.config['TEST_DATA_ROOMS']) as f:
        parsed = json.load(f)
        return [Room(agent) for agent in parsed['agents']]


def parse_course_test_data():
    with open(app.config['TEST_DATA_COURSES']) as f:
        parsed = json.load(f)
        return parsed['courses']


def get_test_script_course(test_script_str):
    for course in parse_course_test_data():
        if course['test_script'] == test_script_str:
            return course


def get_all_eligible_section_ids():
    sql = f"""SELECT DISTINCT(section_id)
              FROM sis_sections
              JOIN rooms ON rooms.location = sis_sections.meeting_location
              WHERE sis_sections.term_id = {app.config['CURRENT_TERM_ID']}
                AND rooms.capability IS NOT NULL
                AND sis_sections.is_principal_listing IS TRUE
                AND deleted_at IS NULL
              ORDER BY section_id ASC;
    """
    app.logger.info(sql)
    ids = []
    result = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    for row in result:
        ids.append(f'{dict(row).get("section_id")}')
    return ids


# SECTION TEST DATA


def get_test_section(test_data):
    sql = f"""SELECT sis_sections.section_id AS ccn,
                     sis_sections.course_name AS code,
                     sis_sections.course_title AS title,
                     sis_sections.instruction_format AS format,
                     sis_sections.section_num AS num
                FROM sis_sections
               WHERE sis_sections.term_id = {app.config['CURRENT_TERM_ID']}
                 AND sis_sections.course_name LIKE '{test_data["dept_code"]} %'
                 AND sis_sections.course_name NOT LIKE '{test_data["dept_code"]} C%'
                 AND sis_sections.instruction_format = 'LEC'
                 AND sis_sections.is_principal_listing IS TRUE
                 AND sis_sections.deleted_at IS NULL
            ORDER BY code, ccn
               LIMIT 1;
    """
    app.logger.info(sql)
    result = db.session.execute(text(sql)).first()
    std_commit(allow_test_environment=True)
    app.logger.info(f'{result}')
    sis_data = {
        'ccn': f'{result["ccn"]}',
        'code': result['code'],
        'title': result['title'],
        'number': f'{result["format"]} {result["num"]}',
        'is_primary': 'TRUE',
        'is_primary_listing': True,
    }
    test_data.update(sis_data)
    return Section(test_data)


def get_test_x_listed_sections(test_data):
    sql = f"""SELECT cross_listings.section_id AS ccn,
                     cross_listings.cross_listed_section_ids[1] AS listing_ccn,
                     sis_sections.course_name AS code,
                     sis_sections.instruction_format AS format,
                     sis_sections.section_num AS num,
                     sis_sections.course_title AS title
                FROM cross_listings
                JOIN sis_sections ON cross_listings.section_id = sis_sections.section_id
               WHERE cross_listings.term_id = {app.config['CURRENT_TERM_ID']}
                 AND sis_sections.term_id = {app.config['CURRENT_TERM_ID']}
                 AND array_length(cross_listings.cross_listed_section_ids, 1) = 1
                 AND sis_sections.instruction_format = 'LEC'
                 AND sis_sections.meeting_location != 'Internet/Online'
                 AND sis_sections.deleted_at IS NULL
            ORDER BY ccn, code
               LIMIT 1;
    """
    app.logger.info(sql)
    result = db.session.execute(text(sql)).first()
    std_commit(allow_test_environment=True)
    app.logger.info(f'{result}')

    sql = f'SELECT course_name FROM sis_sections WHERE section_id = {result["listing_ccn"]};'
    app.logger.info(sql)
    listing_result = db.session.execute(text(sql)).first()
    std_commit(allow_test_environment=True)
    app.logger.info(f'{listing_result}')

    sis_data = {
        'ccn': f'{result["ccn"]}',
        'code': result['code'],
        'title': result['title'],
        'number': f'{result["format"]} {result["num"]}',
        'is_primary_listing': True,
        'listings': [{'ccn': result['listing_ccn'], 'code': listing_result['course_name']}],
    }
    test_data.update(sis_data)
    primary_listing_section = Section(test_data)

    listing_sis_data = {
        'ccn': f'{result["listing_ccn"]}',
        'code': listing_result['course_name'],
        'is_primary_listing': False,
        'listings': [],
    }
    listing_test_data = test_data.copy()
    listing_test_data.update(listing_sis_data)
    secondary_listing_section = Section(listing_test_data)

    return [primary_listing_section, secondary_listing_section]


def delete_sis_sections_rows(section):
    sql = f"DELETE FROM sis_sections WHERE section_id = {section.ccn} AND term_id = {app.config['CURRENT_TERM_ID']};"
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def add_sis_sections_rows(section):
    instruction_format = section.number.split(' ')[0]
    section_num = section.number.split(' ')[1]
    all_instructors = section.instructors + section.proxies
    for instructor in all_instructors:
        instructor_name = f'{instructor.first_name} {instructor.last_name}'
        for meeting in section.meetings:
            room = meeting.room.name.replace("'", "''")
            days = meeting.days.replace(',', '').replace(' ', '')
            start_date = meeting.start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_date = meeting.end_date.strftime('%Y-%m-%d %H:%M:%S')
            start_time = datetime.strptime(meeting.start_time, '%I:%M %p').strftime('%H:%M')
            end_time = datetime.strptime(meeting.end_time, '%I:%M %p').strftime('%H:%M')
            sql = f"""
                INSERT INTO sis_sections (
                    allowed_units, course_name, course_title, created_at, instruction_format, instructor_name,
                    instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date, meeting_end_time,
                    meeting_location, meeting_start_date, meeting_start_time, section_id, section_num, term_id,
                    is_principal_listing
                )
                SELECT
                    '4', '{section.code}', '{section.title}', now(), '{instruction_format}', '{instructor_name}',
                    '{instructor.role}', '{instructor.uid}', TRUE, '{days}', '{end_date}', '{end_time}', '{room}',
                    '{start_date}', '{start_time}', {section.ccn}, '{section_num}', {section.term.id},
                    {str(section.is_primary_listing).upper()}
            """
            app.logger.info(sql)
            db.session.execute(text(sql))
            std_commit(allow_test_environment=True)


def reset_test_data(section):
    delete_sis_sections_rows(section)
    add_sis_sections_rows(section)


def reset_invite_test_data(term, section, instructor=None):
    # So that invitation will be sent to one instructor on a course
    if instructor:
        sql = f"""DELETE FROM sent_emails
                  WHERE term_id = {term.id}
                    AND section_id = {section.ccn}
                    AND recipient_uid = '{instructor.uid}'
                    AND template_type = 'invitation'
        """
    # So that invitations will be sent to all instructors on a course
    else:
        sql = f"""DELETE FROM sent_emails
                  WHERE term_id = {term.id}
                    AND section_id = {section.ccn}
                    AND template_type = 'invitation'
        """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def reset_sign_up_test_data(section):
    reset_test_data(section)
    term_id = app.config['CURRENT_TERM_ID']
    sql = f'DELETE FROM approvals WHERE section_id = {section.ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM scheduled WHERE section_id = {section.ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM sent_emails WHERE section_id = {section.ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM course_preferences WHERE section_id = {section.ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


# ADD/UPDATE LOCATION, SCHEDULE, INSTRUCTORS


def set_meeting_location(section, meeting):
    sql = f"""UPDATE sis_sections
              SET meeting_location = {"'" + meeting.room.name.replace("'", "''") + "'" if meeting.room else "NULL"}
              WHERE section_id = {section.ccn}
                AND term_id = {section.term.id}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def change_course_room(section, old_room=None, new_room=None):
    if old_room:
        old_name = old_room.name.replace("'", "''")
        old = f"= '{old_name}'"
    else:
        old = 'IS NULL'
    if new_room:
        new_name = new_room.name.replace("'", "''")
        new = f"'{new_name}'"
    else:
        new = 'NULL'
    sql = f"""UPDATE sis_sections
              SET meeting_location = {new}
              WHERE section_id = {section.ccn}
                AND term_id = {section.term.id}
                AND meeting_location {old}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def update_course_start_end_dates(section, room, start, end):
    room_name = room.name.replace("'", "''")
    sql = f"""UPDATE sis_sections
              SET meeting_start_date = {"'" + start.strftime('%Y-%m-%d %H:%M:%S') + "'" if start else "NULL"},
                  meeting_end_date = {"'" + end.strftime('%Y-%m-%d %H:%M:%S') + "'" if start else "NULL"}
              WHERE section_id = {section.ccn}
                  AND term_id = {section.term.id}
                  AND meeting_location = '{room_name}'
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def set_course_meeting_days(section, meeting):
    sql = f"""UPDATE sis_sections
              SET meeting_days = {"'" + meeting.days + "'" if meeting.days else "NULL"}
              WHERE section_id = {section.ccn}
                  AND term_id = {section.term.id}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def set_course_meeting_time(section, meeting):
    start_time_str = datetime.strptime(meeting.start_time, '%I:%M %p').strftime('%H:%M') if meeting.start_time else None
    end_time_str = datetime.strptime(meeting.end_time, '%I:%M %p').strftime('%H:%M') if meeting.end_time else None
    sql = f"""UPDATE sis_sections
              SET meeting_start_time = {"'" + start_time_str + "'" if start_time_str else "NULL"},
                  meeting_end_time = {"'" + end_time_str + "'" if end_time_str else "NULL"}
              WHERE section_id = {section.ccn}
                  AND term_id = {section.term.id}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def change_course_instructor(section, old_instructor=None, new_instructor=None):
    conditional = f" AND instructor_uid = '{old_instructor.uid}'" if old_instructor else ''
    if new_instructor:
        sql = f"""UPDATE sis_sections
                  SET instructor_uid = '{new_instructor.uid}',
                      instructor_name = '{new_instructor.first_name} {new_instructor.last_name}',
                      instructor_role_code = '{new_instructor.role}'
                  WHERE section_id = {section.ccn}
                      AND term_id = {section.term.id}
                      {conditional}
        """
    else:
        sql = f"""UPDATE sis_sections
                  SET instructor_uid = NULL,
                      instructor_name = NULL,
                      instructor_role_code = NULL
                  WHERE section_id = {section.ccn}
                      AND term_id = {section.term.id}
                      AND instructor_uid = '{old_instructor.uid}'
        """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def set_instructor_role(section, instructor, role):
    sql = f"""UPDATE sis_sections
              SET instructor_role_code = '{role}'
              WHERE section_id = {section.ccn}
                  AND term_id = {section.term.id}
                  AND instructor_uid = '{instructor.uid}'
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def delete_section(section):
    sql = f"""UPDATE sis_sections
              SET deleted_at = NOW()
              WHERE section_id = {section.ccn}
                AND term_id = {section.term.id}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def restore_section(section):
    sql = f"""UPDATE sis_sections
              SET deleted_at = NULL
              WHERE section_id = {section.ccn}
                AND term_id = {section.term.id}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def get_kaltura_id(recording_schedule, term):
    section = recording_schedule.section
    sql = f"""SELECT kaltura_schedule_id
              FROM scheduled
              WHERE term_id = {term.id}
                AND section_id = {section.ccn}
                AND deleted_at IS NULL
    """
    ids = []
    app.logger.info(f'Checking for Kaltura ID for term {term.id} section {section.ccn}')
    result = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    for row in result:
        ids.append(dict(row).get('kaltura_schedule_id'))
    if len(ids) > 0:
        kaltura_id = ids[0]
        app.logger.info(f'ID is {kaltura_id}')
        recording_schedule.series_id = kaltura_id
        recording_schedule.scheduling_status = RecordingSchedulingStatus.SCHEDULED
        return kaltura_id
    else:
        return None


# COURSE SITES


def get_course_site_ids(section):
    sql = f'SELECT canvas_course_site_id FROM canvas_course_sites WHERE term_id = {section.term.id} AND section_id = {section.ccn}'
    app.logger.info(sql)
    ids = []
    result = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    for row in result:
        ids.append(dict(row).get('canvas_course_site_id'))
    app.logger.info(f'Site IDs are {ids}')
    return ids


def delete_course_site(site_id):
    sql = f'DELETE FROM canvas_course_sites WHERE canvas_course_site_id = {site_id}'
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def reset_email_template_test_data(template_type):
    sql = f"DELETE FROM email_templates WHERE template_type = '{template_type}'"
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def get_next_date(start_date, day_index):
    days_ahead = day_index - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return start_date + timedelta(days_ahead)


def get_room_id(room):
    room = room.name.replace("'", "''")
    sql = f"SELECT id FROM rooms WHERE location = '{room}'"
    app.logger.info(sql)
    ids = []
    result = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    for row in result:
        ids.append(dict(row).get('id'))
    return ids[0]


def get_blackout_date_ranges():
    ranges = []
    for i in app.config['KALTURA_BLACKOUT_DATES']:
        pair = i.split(' - ')
        date_pair = [dateutil.parser.parse(pair[0]).date(), dateutil.parser.parse(pair[1]).date()]
        ranges.append(date_pair)
    return ranges
