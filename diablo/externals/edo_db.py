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

from cx_Oracle import connect, makedsn
from diablo import cachify
from diablo.lib.io import read_file
from flask import current_app as app


@cachify('edo_db/all_courses_{term_id}')
def get_edo_db_courses(term_id, section_ids=None):
    with _edo_db_connection() as connection:
        courses = []
        cursor = connection.cursor()
        if section_ids:
            sql = _sql('get_courses_by_section_ids').replace(':section_ids', ', '.join(section_ids))
        else:
            sql = _sql('get_courses_per_term')
        cursor.execute(sql, term_id=term_id)
        distinct_time_and_place_list = []
        for row in cursor:
            course = _extract_course(row)
            time_and_place = f'{course["days_of_week"]} {course["start_time"]} {course["end_time"]} {course["location"]}'
            if time_and_place not in distinct_time_and_place_list:
                distinct_time_and_place_list.append(time_and_place)
                courses.append(course)
        connection.commit()
        return courses


@cachify('edo_db/instructors_{term_id}')
def get_edo_db_instructors_per_section_id(section_ids, term_id):
    instructors_per_section_id = {}
    count_per_chunk = 1000
    for chunk in range(0, len(section_ids), count_per_chunk):
        with _edo_db_connection() as connection:
            cursor = connection.cursor()
            section_ids_chunk_ = section_ids[chunk:chunk + count_per_chunk]
            section_ids_ = ', '.join(str(m) for m in section_ids_chunk_)
            sql = _sql('get_instructors_per_section_ids').replace(':section_ids', section_ids_)
            cursor.execute(sql, term_id=term_id)
            for row in cursor:
                section_id, instructor = _extract_instructor(row)
                if section_id not in instructors_per_section_id:
                    instructors_per_section_id[section_id] = []
                instructors_per_section_id[section_id].append(instructor)
            connection.commit()
    return instructors_per_section_id


def _edo_db_connection():
    db_user = app.config['EDO_DB_USERNAME']
    db_password = app.config['EDO_DB_PASSWORD']
    db_host = app.config['EDO_DB_HOSTNAME']
    db_port = app.config['EDO_DB_PORT']
    db_name = app.config['EDO_DB_NAME']
    dsn = makedsn(db_host, db_port, sid=db_name)
    return connect(db_user, db_password, dsn, encoding='UTF-8')


def _extract_course(row):
    section_id_ = row[0]
    dept_description_ = row[1]
    catalog_id_ = row[2]
    dept_name_ = row[3]
    course_title_ = row[4]
    end_time_ = row[5]
    location_ = row[6]
    days_of_week_ = row[7]
    start_time_ = row[8]
    instruction_format_ = row[9]
    display_name_ = row[10]
    section_num_ = row[11]

    display_name_ = display_name_ or (f'{dept_name_} {catalog_id_}' if dept_name_ and catalog_id_ else course_title_)
    if section_num_:
        suffix = f'{instruction_format_} {section_num_}' if instruction_format_ else section_num_
        display_name_ = f'{display_name_}, {suffix}'
    return {
        'catalog_id': catalog_id_,
        'dept_description': dept_description_,
        'dept_name': dept_name_,
        'display_name': display_name_,
        'instruction_format': instruction_format_,
        'section_num': section_num_,
        'section_id': section_id_,
        'start_time': start_time_,
        'end_time': end_time_,
        'days_of_week': days_of_week_,
        'location': location_,
    }


def _extract_instructor(row):
    uid = row[0]
    section_id = row[1]
    return section_id, {
        'uid': uid,
        'email': row[2],
        'first_name': row[3],
        'last_name': row[4],
        'dept_description': row[5],
    }


def _sql(name):
    return read_file(f'diablo/sql_edo_db/{name}.sql')
