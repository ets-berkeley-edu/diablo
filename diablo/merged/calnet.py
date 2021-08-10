"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.externals import calnet


@cachify('calnet/user_for_uid_{uid}', timeout=86400)
def get_calnet_user_for_uid(app, uid):
    users = _get_calnet_users(app, [uid])
    return users[uid] if users else None


def get_calnet_users_for_uids(app, uids):
    return _get_calnet_users(app, uids)


def _get_calnet_users(app, uids):
    users_by_uid = {}
    if app.config['DIABLO_ENV'] == 'test':
        for uid in uids:
            fixture_path = f"{app.config['FIXTURES_PATH']}/calnet/user_for_uid_{uid}.json"
            if path.isfile(fixture_path):
                with open(fixture_path) as f:
                    users_by_uid[uid] = json.load(f)
            else:
                users_by_uid[uid] = {'uid': uid}
    else:
        calnet_client = calnet.client(app)
        calnet_results = calnet_client.search_uids(uids)
        for uid in uids:
            calnet_result = next((r for r in calnet_results if r['uid'] == uid), None)
            feed = {
                **_calnet_user_api_feed(calnet_result),
                **{'uid': uid},
            }
            users_by_uid[uid] = feed
    return users_by_uid


def _calnet_user_api_feed(person):
    def _get(key):
        return _get_attribute(person, key)

    uid = _get('uid')
    first_name = _get('first_name')
    last_name = _get('last_name')
    return {
        'deptCode': _get('primary_dept_code') or _get('dept_code'),
        'email': _get('email'),
        'firstName': first_name,
        'isExpiredPerLdap': _get('expired'),
        'lastName': last_name,
        'name': f'{first_name} {last_name}'.strip() if (first_name or last_name) else uid,
        'uid': uid,
    }


def _get_attribute(person, key):
    if not person:
        return None
    elif isinstance(person[key], list):
        return person[key][0]
    else:
        return person[key]
