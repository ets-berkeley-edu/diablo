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

import json
from os import path

from diablo import cachify
from diablo.api.errors import InternalServerError
from diablo.externals import calnet


@cachify('calnet/user_for_uid_{uid}')
def get_calnet_user_for_uid(app, uid):
    users = _get_calnet_users(app, 'uid', [uid])
    return users[uid] if users else None


def get_calnet_users_for_uids(app, uids):
    return _get_calnet_users(app, 'uid', uids)


def _get_calnet_users(app, id_type, ids):
    users_by_id = {}
    if app.config['DIABLO_ENV'] == 'test':
        for id_ in ids:
            fixture_path = f"{app.config['FIXTURES_PATH']}/calnet/user_for_uid_{id_}.json"
            if path.isfile(fixture_path):
                with open(fixture_path) as f:
                    users_by_id[id_] = json.load(f)
            else:
                users_by_id[id_] = {id_type: id_}
    else:
        calnet_client = calnet.client(app)
        if id_type == 'uid':
            calnet_results = calnet_client.search_uids(ids)
        elif id_type == 'csid':
            calnet_results = calnet_client.search_csids(ids)
        else:
            raise InternalServerError(f'get_calnet_users: {id_type} is an invalid id type')

        for id_ in ids:
            calnet_result = next((r for r in calnet_results if r[id_type] == id_), None)
            feed = {
                **_calnet_user_api_feed(calnet_result),
                **{id_type: id_},
            }
            users_by_id[id_] = feed
    return users_by_id


def _calnet_user_api_feed(person):
    def _get(key):
        return _get_attribute(person, key)

    uid = _get('uid')
    return {
        'campusEmail': _get('campus_email'),
        'deptCode': _get_dept_code(person),
        'email': _get('email'),
        'firstName': _get('first_name'),
        'isExpiredPerLdap': _get('expired'),
        'lastName': _get('last_name'),
        'name': _get('name') or uid,
        'title': _get('title'),
        'uid': uid,
    }


def _get_dept_code(p):
    def dept_code_fallback():
        dept_hierarchy = _get_attribute(p, 'dept_unit_hierarchy')
        if dept_hierarchy:
            return dept_hierarchy.rsplit('-', 1)[-1]
        else:
            return None
    return p and (p['primary_dept_code'] or p['dept_code'] or p['calnet_dept_code'] or dept_code_fallback())


def _get_attribute(person, key):
    if not person:
        return None
    elif isinstance(person[key], list):
        return person[key][0]
    else:
        return person[key]
