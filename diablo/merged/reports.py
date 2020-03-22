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

import csv
from datetime import datetime
import logging

from diablo import BASE_DIR
from diablo.externals.edo_db import get_edo_db_courses, get_edo_db_instructors_per_section_id
from diablo.externals.salesforce import get_all_contacts, get_all_courses, get_all_salesforce_rooms
from diablo.lib.salesforce_utils import convert_military_time, days_of_week_for_salesforce, \
    get_uids_of_salesforce_contacts, is_course_in_capture_enabled_room
from flask import current_app as app


def verify_salesforce_data():
    term_id = app.config['CURRENT_TERM_ID']
    logging.info(f'Verifying Salesforce data where term_id = {term_id}.')

    edo_db_courses_per_section_id = dict((int(c['section_id']), c) for c in get_edo_db_courses(term_id))
    edo_db_instructors_per_section_id = get_edo_db_instructors_per_section_id(
        section_ids=list(edo_db_courses_per_section_id.keys()),
        term_id=term_id,
    )
    salesforce_contacts_per_id = dict((p['Id'], p) for p in get_all_contacts())
    salesforce_courses_per_section_id = dict((int(c['CCN__c']), c) for c in get_all_courses())
    salesforce_locations_per_id = dict((r['Id'], r) for r in get_all_salesforce_rooms())

    path_to_stale_data_report = _write_csv_report(
        'stale-data-in-salesforce-course-data',
        _report_on_stale_data_in_salesforce(
            edo_db_courses_per_section_id=edo_db_courses_per_section_id,
            edo_db_instructors_per_section_id=edo_db_instructors_per_section_id,
            salesforce_contacts_per_id=salesforce_contacts_per_id,
            salesforce_courses_per_section_id=salesforce_courses_per_section_id,
            salesforce_locations_per_id=salesforce_locations_per_id,
        ),
    )
    path_to_courses_missing_report = _write_csv_report(
        'eligible_courses_missing_in_salesforce',
        _report_on_eligible_courses_missing_in_salesforce(
            edo_db_courses=edo_db_courses_per_section_id.values(),
            salesforce_courses_per_section_id=salesforce_courses_per_section_id,
            salesforce_locations=salesforce_locations_per_id.values(),
        ),
    )
    logging.info(f'Salesforce verification is done.')
    return path_to_stale_data_report, path_to_courses_missing_report


def write_csv_report(report_name, report):
    if report:
        term_id = app.config['CURRENT_TERM_ID']
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        headers = report[0].keys()
        path_to_file = f'{BASE_DIR}/log/{report_name}-{term_id}_{now}.csv'
        with open(path_to_file, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in report:
                writer.writerow(row.values())
        return path_to_file
    else:
        logging.warning('CSV file not created because report has zero rows.')
        return None


def _report_on_stale_data_in_salesforce(
        edo_db_courses_per_section_id,
        edo_db_instructors_per_section_id,
        salesforce_contacts_per_id,
        salesforce_courses_per_section_id,
        salesforce_locations_per_id,
):
    report = []
    for section_id_, salesforce_course in salesforce_courses_per_section_id.items():
        uids_of_salesforce_contacts = get_uids_of_salesforce_contacts(salesforce_course, salesforce_contacts_per_id)
        salesforce_room = salesforce_locations_per_id[salesforce_course['Room__c']]
        salesforce_room = f'{salesforce_room["Building__c"]} {salesforce_room["Room_Number_Text__c"]}'
        salesforce_schedule = _describe_course_schedule(
            salesforce_course['Start_Time__c'],
            salesforce_course['End_Time__c'],
            salesforce_course['Schedule_Days__c'],
        )

        def _append_to_report(
                errors_,
                edo_db_instructor_uids_=None,
                edo_db_room_=None,
                edo_db_schedule_=None,
        ):
            report.append({
                'salesforce_id': salesforce_course['Id'],
                'section_id': section_id_,
                'course_title': salesforce_course['Course_Title__c'],
                'errors': errors_,
                'edo_db_instructors': ', '.join(edo_db_instructor_uids_) if edo_db_instructor_uids_ else '',
                'edo_db_room': edo_db_room_,
                'edo_db_schedule': edo_db_schedule_,
                'salesforce_contacts': ', '.join(uids_of_salesforce_contacts),
                'salesforce_room': salesforce_room,
                'salesforce_schedule': salesforce_schedule,
            })

        edo_db_course = edo_db_courses_per_section_id[section_id_]
        if edo_db_course:
            errors = []
            # Room check
            if edo_db_course['location'] != salesforce_room:
                errors.append('Rooms')
            # Time check
            edo_db_schedule = _describe_course_schedule(
                convert_military_time(edo_db_course['start_time']),
                convert_military_time(edo_db_course['end_time']),
                days_of_week_for_salesforce(edo_db_course['days_of_week']),
            )
            if edo_db_schedule != salesforce_schedule:
                errors.append('Schedule')

            # Compare instructors
            edo_db_instructors = edo_db_instructors_per_section_id.get(section_id_, [])
            edo_db_instructor_uids = [i['uid'] for i in edo_db_instructors]
            if sorted(edo_db_instructor_uids) != sorted(uids_of_salesforce_contacts):
                errors.append('Instructor UIDs')

            if errors:
                _append_to_report(
                    errors_=', '.join(errors),
                    edo_db_instructor_uids_=edo_db_instructor_uids,
                    edo_db_room_=edo_db_course['location'],
                    edo_db_schedule_=edo_db_schedule,
                )
        else:
            _append_to_report(errors_='NO MATCH IN EDO DB')
    return report


def _report_on_eligible_courses_missing_in_salesforce(
        edo_db_courses,
        salesforce_courses_per_section_id,
        salesforce_locations,
):
    report = []
    for edo_db_course in edo_db_courses:
        is_course_capture_enabled = is_course_in_capture_enabled_room(edo_db_course, salesforce_locations)
        if is_course_capture_enabled and edo_db_course['section_id'] not in salesforce_courses_per_section_id:
            report.append(edo_db_course)
    return report


def _describe_course_schedule(start_time, end_time, days_of_week):
    return f'{start_time} to {end_time}, on {days_of_week}'


def _write_csv_report(report_name, report):
    if report:
        path_to_csv = write_csv_report(report_name, report)
        logging.info(f'{len(report)} rows in report {path_to_csv}')
        return path_to_csv
    else:
        logging.info(f'\'{report_name}\' report is empty. No problem found.')
        return None
