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

import logging

from diablo.externals.salesforce import bulk_upsert_contacts, bulk_upsert_courses, get_all_contacts, get_all_courses, \
    get_all_rooms
from diablo.lib.salesforce_utils import get_salesforce_location_id, is_course_in_capture_enabled_room, \
    prepare_salesforce_contact_record, prepare_salesforce_course_record
from diablo.merged.sis import get_course_and_instructors
from flask import current_app as app


class CourseDataMover:

    def __init__(self, term_id):
        self.term_id = term_id
        self.salesforce_locations = get_all_rooms()
        self.salesforce_ids_per_section_id = _load_salesforce_ids_per_section_id()
        self.contact_ids_per_uid = _load_contact_ids_per_uid()
        logging.info(f"""
            Salesforce returned
            {len(self.salesforce_ids_per_section_id)} courses,
            {len(self.salesforce_locations)} locations, and
            {len(self.contact_ids_per_uid)} persons.
        """)

    def run(self, section_ids=None):
        course_sections = get_course_and_instructors(self.term_id, section_ids)
        if section_ids:
            app.logger.info(f'CDM will only process section ids {", ".join(section_ids)}')
        else:
            app.logger.info(f'EDO db query return {len(course_sections)} courses.')
        courses_updated = self._update_courses_in_salesforce(course_sections)
        app.logger.info(f'{len(courses_updated)} courses updated in Salesforce.')

    def _update_courses_in_salesforce(self, edo_db_courses):
        location_ids_per_section_id = self._get_salesforce_location_ids_per_section_id(edo_db_courses)

        def _requires_update(edo_db_course_):
            section_id_ = str(edo_db_course_['section_id'])
            if section_id_ in self.salesforce_ids_per_section_id:
                return True
            else:
                return edo_db_course['instructors'] and is_course_in_capture_enabled_room(
                    edo_db_course_,
                    self.salesforce_locations,
                )
        # Upsert contacts in Salesforce
        contacts_batch = []
        for edo_db_course in edo_db_courses:
            if _requires_update(edo_db_course):
                for instructor in edo_db_course['instructors']:
                    uid_ = str(instructor['uid'])
                    if uid_ not in [c['Calnet_UID__c'] for c in contacts_batch]:
                        salesforce_contact = prepare_salesforce_contact_record(instructor)
                        if uid_ in self.contact_ids_per_uid:
                            salesforce_contact['Id'] = self.contact_ids_per_uid[uid_]
                        contacts_batch.append(salesforce_contact)
        bulk_upsert_contacts(contacts_batch)
        self.contact_ids_per_uid = _load_contact_ids_per_uid()

        courses_batch = []
        for edo_db_course in edo_db_courses:
            if _requires_update(edo_db_course):
                section_id = edo_db_course['section_id']
                instructor_uids = [instructor['uid'] for instructor in edo_db_course['instructors']]
                salesforce_course = prepare_salesforce_course_record(
                    edo_db_course,
                    [self.contact_ids_per_uid[uid] for uid in instructor_uids],
                    location_ids_per_section_id[section_id],
                )
                if section_id in self.salesforce_ids_per_section_id:
                    salesforce_course['Id'] = self.salesforce_ids_per_section_id[section_id]
                courses_batch.append(salesforce_course)
        if courses_batch:
            bulk_upsert_courses(courses_batch)
        return courses_batch

    def _get_salesforce_location_ids_per_section_id(self, edo_db_courses):
        location_ids_per_section_id = {}
        for edo_db_course in edo_db_courses:
            section_id = edo_db_course['section_id']
            location_ids_per_section_id[section_id] = get_salesforce_location_id(
                edo_db_course,
                self.salesforce_locations,
            )
        return location_ids_per_section_id


def _load_contact_ids_per_uid():
    contact_ids_per_uid = {}
    for person in get_all_contacts():
        uid = person['Calnet_UID__c']
        contact_ids_per_uid[uid] = person['Id']
    return contact_ids_per_uid


def _load_salesforce_ids_per_section_id():
    salesforce_ids_per_section_id = {}
    for salesforce_course in get_all_courses():
        section_id = salesforce_course['CCN__c']
        salesforce_ids_per_section_id[section_id] = salesforce_course['Id']
    return salesforce_ids_per_section_id
