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

from diablo import BASE_DIR, cache, db, std_commit
from diablo.models.admin_user import AdminUser
from diablo.models.sign_up import SignUp
from flask import current_app as app
from sqlalchemy.sql import text


_test_users = [
    {
        'uid': '2040',
    },
]


def clear():
    with open(app.config['BASE_DIR'] + '/scripts/db/drop_schema.sql', 'r') as ddlfile:
        db.session().execute(text(ddlfile.read()))
        std_commit()


def load():
    _load_schemas()
    _create_users()
    _create_sign_ups()
    _cache_externals()
    return db


def _cache_externals():
    with open(f'{BASE_DIR}/fixtures/salesforce_capture_enabled_rooms.json', 'r') as file:
        cache.set('salesforce_capture_enabled_rooms', json.loads(file.read()))
    for uid in ['2040', '1015674', '8765432']:
        with open(f'{BASE_DIR}/fixtures/calnet_user_for_uid_{uid}.json', 'r') as file:
            cache.set(f'calnet_user_for_uid_{uid}', json.loads(file.read()))


def _load_schemas():
    """Create DB schema from SQL file."""
    with open(app.config['BASE_DIR'] + '/scripts/db/schema.sql', 'r') as ddlfile:
        db.session().execute(text(ddlfile.read()))
        std_commit()


def _create_users():
    for test_user in _test_users:
        db.session.add(AdminUser(uid=test_user['uid']))
    std_commit(allow_test_environment=True)


def _create_sign_ups():
    db.session.add(
        SignUp(
            term_id=app.config['CURRENT_TERM'],
            section_id=28602,
            admin_approval_uid=None,
            instructor_approval_uids=['8765432'],
            publish_type_='canvas',
            recording_type_='presentation_audio',
            requires_multiple_approvals=True,
        ),
    )
    std_commit(allow_test_environment=True)


if __name__ == '__main__':
    import diablo.factory
    diablo.factory.create_app()
    load()
