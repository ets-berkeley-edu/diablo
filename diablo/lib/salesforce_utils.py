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

from flask import current_app as app

days_of_week_translation = {
    'SU': 'Sunday',
    'MO': 'Monday',
    'TU': 'Tuesday',
    'WE': 'Wednesday',
    'TH': 'Thursday',
    'FR': 'Friday',
    'SA': 'Saturday',
}


def get_salesforce_location_id(edo_db_course, all_salesforce_locations):
    id_ = None
    course_location_ = _normalize_edo_db_location(edo_db_course)
    for salesforce_location in all_salesforce_locations:
        if course_location_ == normalize_salesforce_location(salesforce_location):
            id_ = salesforce_location['Id']
            break
    return id_


def prepare_salesforce_course_record(edo_db_course, salesforce_contact_ids, salesforce_location_id):
    section_id_ = edo_db_course['section_id']
    record = {
        'CCN__c': section_id_,
        'CloseDate': app.config['LAST_DAY_OF_INSTRUCTION'],
        'Course_Title__c': edo_db_course['display_name'],
        'End_Time__c': convert_military_time(edo_db_course['end_time']),
        'Instructor_1__c': None,
        'Instructor_2__c': None,
        'Instructor_3__c': None,
        'Instructor_4__c': None,
        'Instructor_5__c': None,
        'Instructor_6__c': None,
        'Name': edo_db_course['display_name'],
        'RecordTypeId': app.config['SALESFORCE_COURSE_CAPTURE_RECORD_TYPE_ID'],
        'Room__c': salesforce_location_id,
        'Schedule_Days__c': days_of_week_for_salesforce(edo_db_course['days_of_week']),
        'Section__c': edo_db_course['section_num'],
        'StageName': 'Prospecting',
        'Start_Time__c': convert_military_time(edo_db_course['start_time']),
        'Type': 'Course Capture',
    }
    for index, salesforce_contact_id in enumerate(salesforce_contact_ids):
        record[f'Instructor_{index + 1}__c'] = salesforce_contact_id
    return record


def convert_military_time(edo_db_military_time):
    military_time_ = edo_db_military_time and edo_db_military_time.strip()
    if military_time_:
        hours, minutes = military_time_.strip().split(':')
        hours, minutes = int(hours), int(minutes)
        if hours < 0 or hours > 24 or minutes < 0 or minutes > 59 or (hours == 24 and minutes > 0):
            raise ValueError(f'Invalid military time: {edo_db_military_time}')
        # Salesforce standard: 'a' for AM, 'p' for PM
        am_or_pm = 'am' if hours < 12 or hours == 24 else 'pm'
        if hours > 12:
            hours -= 12
        return f'%02d:%02d{am_or_pm}' % (hours, minutes)
    else:
        return None


def get_uids_of_salesforce_contacts(salesforce_course, salesforce_contacts_per_id):
    uids = []
    for index_ in range(6):
        id_ = salesforce_course[f'Instructor_{index_ + 1}__c']
        if id_ in salesforce_contacts_per_id:
            uids.append(salesforce_contacts_per_id[id_]['Calnet_UID__c'])
    return uids


def days_of_week_for_salesforce(edo_db_days):
    trimmed = edo_db_days and edo_db_days.strip().upper()
    if trimmed:
        days = []
        for (key, day) in days_of_week_translation.items():
            if key in trimmed:
                days.append(day)
                trimmed = trimmed.replace(key, '', 1)
        if len(trimmed) or not len(days):
            # Error if edo_db_days has extraneous string or zero days
            raise ValueError(f'Invalid edo_db_days: {edo_db_days}')
        return ', '.join(days)
    else:
        return None


def is_course_in_capture_enabled_room(edo_db_course, salesforce_locations):
    locations = list(filter(lambda r: r['capability'], salesforce_locations))
    capture_enabled_location_names = dict((normalize_salesforce_location(r), r) for r in locations)
    return _normalize_edo_db_location(edo_db_course) in capture_enabled_location_names


def _normalize_edo_db_location(edo_db_course):
    location = edo_db_course['location']
    if 'Genetics & Plant Bio' in location:
        location = location.replace('Genetics & Plant Bio', 'GPB')
    return ''.join(location.split()).lower()


def normalize_salesforce_location(record):
    location_name = f'{record["building"]} {record["roomNumber"]}'
    return ''.join(location_name.split()).lower()


def prepare_salesforce_contact_record(instructor):
    return {
        'Calnet_UID__c': instructor['uid'],
        'Department': instructor['dept_description'],
        'Email': instructor['email'],
        'FirstName': instructor['first_name'],
        'LastName': instructor['last_name'],
        'Role__c': 'Faculty',
    }
