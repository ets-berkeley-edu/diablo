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
import json
import os
import re

from diablo import db
from diablo.lib.db import resolve_sql_template_string
from flask import current_app as app
from sqlalchemy.sql import text


"""Loch queries."""


def get_loch_basic_attributes(uids):
    if os.environ.get('DIABLO_ENV') == 'test':
        return _read_fixture(f"{app.config['FIXTURES_PATH']}/loch_ness/basic_attributes.json")

    query = resolve_sql_template_string("""SELECT * FROM dblink('{dblink_nessie_rds}',$NESSIE$
                SELECT ldap_uid, sid, first_name, last_name, email_address
                  FROM sis_data.basic_attributes
                  WHERE ldap_uid = ANY(:uids)
            $NESSIE$)
            AS nessie_basic_attributes (
                uid VARCHAR,
                csid VARCHAR,
                first_name VARCHAR,
                last_name VARCHAR,
                email VARCHAR
            )
            """)
    try:
        results = db.session().execute(
            text(query),
            {'uids': uids},
        ).all()
        app.logger.info(f'Loch Ness basic attributes query returned {len(results)} results for {len(uids)} uids.')
        return results
    except Exception as e:
        app.logger.exception(e)


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
                  AND affiliations LIKE '%-TYPE-%' AND affiliations NOT LIKE '%TYPE-SPA%'
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


def _read_fixture(fixture_path):
    results = []
    if os.path.isfile(fixture_path):
        with open(fixture_path) as f:
            results = json.load(f)
    return results
