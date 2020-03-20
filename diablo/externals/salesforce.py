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

from diablo import BASE_DIR, cachify, skip_when_pytest
from diablo.lib.io import read_file
from flask import current_app as app
from simple_salesforce import Salesforce

CACHE_TIMEOUT_MINUTES = 30


@cachify('salesforce/capture_enabled_rooms', timeout=CACHE_TIMEOUT_MINUTES)
def get_capture_enabled_rooms():
    with open(f'{BASE_DIR}/diablo/soql/get_all_enabled_rooms.soql', 'r') as file:
        result = _get_client().query(file.read())
        return [_room_to_json(room) for room in result['records']]


@cachify('salesforce/all_courses', timeout=CACHE_TIMEOUT_MINUTES)
def get_all_courses():
    salesforce_term_id = app.config['SALESFORCE_PARENT_TERM_ID']
    result = _query('get_courses_per_term', {'salesforce_term_id': salesforce_term_id})
    courses = result['records']
    app.logger.info(f'Salesforce returned {len(courses)} courses.')
    return courses


@cachify('salesforce/get_all_eligible_courses', timeout=30)
def get_all_eligible_courses():
    salesforce_term_id = app.config['SALESFORCE_PARENT_TERM_ID']
    result = _query('get_eligible_courses_per_term', {'salesforce_term_id': salesforce_term_id})
    courses = result['records']
    app.logger.info(f'Salesforce returned {len(courses)} eligible courses.')
    return courses


@cachify('salesforce/all_contacts', timeout=CACHE_TIMEOUT_MINUTES)
def get_all_contacts():
    contacts = _query('get_all_contacts')['records']
    app.logger.info(f'Salesforce returned {len(contacts)} contacts.')
    return contacts


@cachify('salesforce/all_rooms', timeout=CACHE_TIMEOUT_MINUTES)
def get_all_rooms():
    result = _query('get_all_rooms')
    return [_room_to_json(room) for room in result['records']]


@skip_when_pytest()
def bulk_upsert_courses(batch):
    for result in _get_client().bulk.Opportunity.upsert(batch, 'Id'):
        if result['success'] is not True:
            raise SystemError(f'Failed to upsert course in Salesforce. Salesforce API response: {result}')


@skip_when_pytest()
def bulk_upsert_contacts(batch):
    for result in _get_client().bulk.Contact.upsert(batch, 'Id'):
        if result['success'] is not True:
            raise SystemError(f'Failed to upsert Salesforce contact. Salesforce API response: {result}')


def test_salesforce_connection():
    return bool(_get_client().query('SELECT Id FROM Locations__c WHERE Id = null'))


def _get_client():
    return Salesforce(
        username=app.config['SALESFORCE_USERNAME'],
        password=app.config['SALESFORCE_PASSWORD'],
        domain=app.config['SALESFORCE_DOMAIN'],
        security_token=app.config['SALESFORCE_TOKEN'],
    )


def _translate_salesforce_building(building_name):
    return 'Genetics & Plant Bio' if building_name == 'GPB' else building_name


def _soql(soql_query_name):
    return read_file(f'diablo/soql/{soql_query_name}.soql')


def _query(soql_query_name, args=None):
    soql = _soql(soql_query_name)
    if args:
        for key, value in args.items():
            soql = soql.replace(f':{key}', value)
    return _get_client().query(soql)


def _room_to_json(room):
    return {
        'building': _translate_salesforce_building(room['Building__c']),
        'roomNumber': room['Room_Number_Text__c'],
        'capabilities': room['Recording_Capabilities__c'],
    }
