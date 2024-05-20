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
from datetime import datetime
import json
import os
import re

from dateutil.tz import tzutc
from diablo import db
from flask import current_app as app
import pytz
from sqlalchemy.sql import text


"""Generic utilities."""


def default_timezone():
    return pytz.timezone(app.config['TIMEZONE'])


def json_objects_to_dict(json_objects, field_name_of_key):
    items_per_key = {}
    for json_object in json_objects:
        key = json_object[field_name_of_key]
        if key not in items_per_key:
            items_per_key[key] = []
        items_per_key[key].append(json_object)
    return items_per_key


def localize_datetime(dt):
    return dt.astimezone(pytz.timezone(app.config['TIMEZONE']))


def localized_timestamp_to_utc(_str, date_format='%Y-%m-%dT%H:%M:%S'):
    naive_datetime = datetime.strptime(_str, date_format)
    localized_datetime = pytz.timezone(app.config['TIMEZONE']).localize(naive_datetime)
    return localized_datetime.astimezone(pytz.utc)


def objects_to_dict_organized_by_section_id(objects):
    per_section_id = {}
    for obj in objects:
        key = obj.section_id
        if obj.section_id not in per_section_id:
            per_section_id[key] = []
        per_section_id[key].append(obj)
    return per_section_id


def to_isoformat(value):
    return value and value.astimezone(tzutc()).isoformat()


def epoch_time_to_isoformat(epoch_time):
    return epoch_time and datetime.fromtimestamp(epoch_time, tz=default_timezone()).isoformat()


def utc_now():
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def format_days(days):
    n = 2
    return [(days[i:i + n]) for i in range(0, len(days), n)] if days else []


def format_time(military_time):
    return datetime.strptime(military_time, '%H:%M').strftime('%I:%M %p').lower().lstrip('0') if military_time else None


def get_eb_environment():
    return app.config['EB_ENVIRONMENT'] if 'EB_ENVIRONMENT' in app.config else None


def get_names_of_days(day_codes):
    names_by_code = {
        'mo': 'Monday',
        'tu': 'Tuesday',
        'we': 'Wednesday',
        'th': 'Thursday',
        'fr': 'Friday',
        'sa': 'Saturday',
        'su': 'Sunday',
    }
    return [names_by_code.get(day_code[:2].lower()) for day_code in day_codes or ()]


def get_loch_basic_attributes_by_uid_or_email(snippet, limit=20):
    if not snippet:
        return []
    if os.environ.get('DIABLO_ENV') == 'test':
        return _read_fixture(f"{app.config['FIXTURES_PATH']}/loch_ness/basic_attributes_for_snippet_{snippet}.json")

    query_filter, params = parse_search_snippet(snippet)
    params['limit'] = limit
    query = f"""SELECT * FROM dblink('{app.config['DBLINK_NESSIE_RDS']}',$NESSIE$
                SELECT ldap_uid, sid, first_name, last_name, email_address
                  FROM sis_data.basic_attributes
                  {query_filter}
                  LIMIT :limit
            $NESSIE$)
            AS nessie_basic_attributes (
                uid VARCHAR,
                csid VARCHAR,
                first_name VARCHAR,
                last_name VARCHAR,
                email VARCHAR
            )
            """
    try:
        results = db.session().execute(text(query), params).all()
        app.logger.info(f'Loch Ness basic attributes query returned {len(results)} results (snippet={snippet}).')
        return results
    except Exception as e:
        app.logger.exception(e)


def parse_search_snippet(snippet):
    params = {}
    words = list(set(snippet.lower().split()))
    # A single numeric string indicates a UID search.
    if len(words) == 1 and re.match(r'^\d+$', words[0]):
        query_filter = ' WHERE ldap_uid LIKE :uid_prefix'
        params.update({'uid_prefix': f'{words[0]}%'})
    # Otherwise search by email.
    else:
        query_filter = ' WHERE email_address LIKE :email_prefix'
        params.update({'email_prefix': f'{words[0]}%'})
    return query_filter, params


def readable_join(items):
    return (f"{', '.join(items[:-1])} and {items[-1]}" if len(items) > 1 else items[0]) if len(items or []) else ''


def resolve_xml_template(xml_filename):
    with open(app.config['BASE_DIR'] + f'/diablo/xml_templates/{xml_filename}', encoding='utf-8') as file:
        template_string = file.read()
    return resolve_xml_template_string(template_string)


def resolve_xml_template_string(template_string):
    return template_string.format(
        **{
            'kmc_id': app.config['CANVAS_LTI_KEY'],
        },
    )


def safe_strftime(date, date_format):
    return datetime.strftime(date, date_format) if date else None


def _read_fixture(fixture_path):
    results = []
    if os.path.isfile(fixture_path):
        with open(fixture_path) as f:
            results = json.load(f)
    return results
