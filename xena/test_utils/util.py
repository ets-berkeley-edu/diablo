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

from datetime import datetime, timedelta
import json
import os

import dateutil.parser
from diablo import db, std_commit
from flask import current_app as app
from sqlalchemy import text
from xena.models.recording_scheduling_status import RecordingSchedulingStatus
from xena.models.room import Room
from xena.models.section import Section
from xena.models.term import Term


def get_xena_browser():
    return app.config['XENA_BROWSER']


def get_xena_browser_headless():
    return app.config['XENA_BROWSER_HEADLESS']


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


def get_username():
    return os.getenv('USERNAME')


def get_password():
    return os.getenv('PASSWORD')


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
                 AND (sis_sections.instructor_role_code IN ('ICNT', 'PI', 'TNIC') OR sis_sections.instructor_role_code IS NULL)
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


def get_test_instructors(test_section_data, uids_to_exclude=None):
    uids = []
    if uids_to_exclude:
        for u in uids_to_exclude:
            uids.append(f"'{u}'")
    clause = f" AND instructor_uid NOT IN ({', '.join(uids)})" if uids else ''
    sql = f"""SELECT sis_sections.instructor_uid
                FROM sis_sections
                JOIN instructors ON instructors.uid = sis_sections.instructor_uid
               WHERE sis_sections.term_id = '{Term().id}'
                 AND sis_sections.instructor_name IS NOT NULL
                 AND instructors.first_name IS NOT NULL
                 AND sis_sections.instructor_name != ' '
                 AND instructors.first_name != ' '
                 AND sis_sections.instructor_name != ''
                 AND instructors.first_name != ''
                 AND sis_sections.instructor_role_code = 'PI'
                 AND sis_sections.is_primary IS TRUE
                 {clause}
            ORDER BY RANDOM()
               LIMIT {len(test_section_data['instructors'] + test_section_data['proxies'])};
    """
    app.logger.info(sql)
    result = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    uids = []
    for row in result:
        uids.append(f"'{row['instructor_uid']}'")
    sql = f"""SELECT uid,
                     first_name,
                     last_name,
                     email
                FROM instructors
               WHERE uid IN ({', '.join(uids)})
    """
    app.logger.info(sql)
    results = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    test_user_data = []
    for row in results:
        data = {
            'uid': row['uid'],
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'email': row['email'],
        }
        test_user_data.append(data)

    test_instructor_data = test_user_data[:len(test_section_data['instructors'])] if test_section_data['instructors'] else []
    for i in test_instructor_data:
        idx = test_instructor_data.index(i)
        i.update({'role': test_section_data['instructors'][idx]['role']})
        app.logger.info(f'Instructor: {i}')
    test_section_data['instructors'] = test_instructor_data

    test_proxy_data = test_user_data[len(test_section_data['instructors']):] if test_section_data['proxies'] else []
    for p in test_proxy_data:
        idx = test_proxy_data.index(p)
        p.update({'role': test_section_data['proxies'][idx]['role']})
        app.logger.info(f'Proxy: {p}')
    test_section_data['proxies'] = test_proxy_data


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
    get_test_instructors(test_data)
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
    get_test_instructors(test_data)
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
            schedule = meeting.meeting_schedule
            days = schedule.days.replace(',', '').replace(' ', '')
            start_date = schedule.start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_date = schedule.end_date.strftime('%Y-%m-%d %H:%M:%S')
            start_time = datetime.strptime(schedule.start_time, '%I:%M %p').strftime('%H:%M')
            end_time = datetime.strptime(schedule.end_time, '%I:%M %p').strftime('%H:%M')
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


def reset_sent_email_test_data(section, instructor=None, templates=None):
    if templates:
        temps = [t.value['type'] for t in templates]
        sql_templates = ''
        for t in temps:
            sql_templates += f"'{t}', "
        temp_clause = f' AND template_type IN ({sql_templates[0:-2]})'
    else:
        temp_clause = ''
    if instructor:
        inst_clause = f" AND recipient_uid = '{instructor.uid}'"
    else:
        inst_clause = ''
    sql = f"""DELETE FROM sent_emails
                    WHERE term_id = {section.term.id}
                      AND section_id = {section.ccn}{temp_clause}{inst_clause}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def get_sent_email_count(template, section, instructor=None):
    if instructor:
        sql = f"""SELECT COUNT(*)
                    FROM sent_emails
                   WHERE term_id = {section.term.id}
                     AND section_id = {section.ccn}
                     AND recipient_uid = '{instructor.uid}'
                     AND template_type = '{template.value['type']}'
        """
    else:
        sql = f"""SELECT COUNT(*)
                    FROM sent_emails
                   WHERE term_id = {section.term.id}
                     AND section_id = {section.ccn}
                     AND template_type = '{template.value['type']}'
        """
    app.logger.info(sql)
    result = db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    count = result.fetchone()[0]
    return count


def reset_section_test_data(section):
    reset_test_data(section)
    term_id = app.config['CURRENT_TERM_ID']
    sql = f'DELETE FROM approvals WHERE section_id = {section.ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM scheduled WHERE section_id = {section.ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM schedule_updates WHERE section_id = {section.ccn} AND term_id = {term_id}'
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


def change_course_room(section, meeting, new_room=None):
    if meeting.room:
        old_name = meeting.room.name.replace("'", "''")
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
    meeting.room = new_room


def update_course_start_end_dates(section, meeting, new_schedule):
    room_name = meeting.room.name.replace("'", "''")
    old_start = meeting.meeting_schedule.start_date
    old_end = meeting.meeting_schedule.end_date
    new_start = new_schedule.start_date
    new_end = new_schedule.end_date
    sql = f"""UPDATE sis_sections
                 SET meeting_start_date = {"'" + new_start.strftime('%Y-%m-%d %H:%M:%S') + "'" if new_start else "NULL"},
                     meeting_end_date = {"'" + new_end.strftime('%Y-%m-%d %H:%M:%S') + "'" if new_end else "NULL"}
               WHERE section_id = {section.ccn}
                 AND term_id = {section.term.id}
                 AND meeting_location = '{room_name}'
                 AND meeting_start_date = {"'" + old_start.strftime('%Y-%m-%d %H:%M:%S') + "'" if old_start else "NULL"}
                 AND meeting_end_date = {"'" + old_end.strftime('%Y-%m-%d %H:%M:%S') + "'" if old_end else "NULL"}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
    meeting.meeting_schedule.start_date = new_start
    meeting.meeting_schedule.end_date = new_end


def set_course_meeting_days(section, meeting):
    schedule = meeting.meeting_schedule
    sql = f"""UPDATE sis_sections
                 SET meeting_days = {"'" + schedule.days + "'" if schedule.days else "NULL"}
               WHERE section_id = {section.ccn}
                 AND term_id = {section.term.id}
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def set_course_meeting_time(section, meeting):
    schedule = meeting.meeting_schedule
    start_time_str = datetime.strptime(schedule.start_time, '%I:%M %p').strftime('%H:%M') if schedule.start_time else None
    end_time_str = datetime.strptime(schedule.end_time, '%I:%M %p').strftime('%H:%M') if schedule.end_time else None
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
    if old_instructor:
        section.instructors.remove(old_instructor)
    if new_instructor:
        section.instructors.append(new_instructor)


def delete_course_instructor_row(section, instructor):
    sql = f"""DELETE FROM sis_sections
                    WHERE section_id = {section.ccn}
                      AND term_id = {section.term.id}
                      AND instructor_uid = '{instructor.uid}'
    """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def delete_term_instructor_rows(term, instructor):
    sql = f"""DELETE FROM sis_sections
                    WHERE term_id = {term.id}
                      AND instructor_uid = '{instructor.uid}'
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


def switch_principal_listing(old_primary, new_primary):
    sql_1 = f"""UPDATE sis_sections
                   SET is_principal_listing = FALSE
                 WHERE section_id = {old_primary.ccn}
                   AND term_id = {old_primary.term.id}
    """
    app.logger.info(sql_1)
    db.session.execute(text(sql_1))
    std_commit(allow_test_environment=True)
    sql_2 = f"""UPDATE sis_sections
                   SET is_principal_listing = TRUE
                 WHERE section_id = {new_primary.ccn}
                   AND term_id = {new_primary.term.id}
    """
    app.logger.info(sql_2)
    db.session.execute(text(sql_2))
    std_commit(allow_test_environment=True)
    sql_3 = f"""UPDATE cross_listings
                   SET section_id = {new_primary.ccn},
                       cross_listed_section_ids = ARRAY [{old_primary.ccn}]
                 WHERE section_id = {old_primary.ccn}
                   AND term_id = {old_primary.term.id}
    """
    app.logger.info(sql_3)
    db.session.execute(text(sql_3))
    std_commit(allow_test_environment=True)


def get_kaltura_id(recording_schedule):
    section = recording_schedule.section
    meeting = recording_schedule.meeting
    schedule = meeting.meeting_schedule
    sql = f"""SELECT kaltura_schedule_id
                FROM scheduled
                JOIN rooms ON rooms.id = scheduled.room_id
               WHERE scheduled.term_id = {section.term.id}
                 AND scheduled.section_id = {section.ccn}
                 AND scheduled.meeting_start_date = '{schedule.start_date.strftime('%Y-%m-%d %H:%M:%S')}'
                 AND scheduled.meeting_end_date = '{schedule.end_date.strftime('%Y-%m-%d %H:%M:%S')}'
                 AND rooms.location = '{meeting.room.name}'
                 AND scheduled.deleted_at IS NULL
    """
    ids = []
    app.logger.info(f'Checking for Kaltura ID for term {section.term.id} section {section.ccn}')
    app.logger.info(sql)
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
