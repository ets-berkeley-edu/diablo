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

import glob
import json

from diablo import BASE_DIR, cache, db, std_commit
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.data_loch_sync_job import DataLochSyncJob
from diablo.jobs.update_rooms_job import UpdateRoomsJob
from diablo.lib.util import utc_now
from diablo.models.admin_user import AdminUser
from diablo.models.email_template import EmailTemplate
from diablo.models.room import Room
from diablo.models.sent_email import SentEmail
from flask import current_app as app
from sqlalchemy.sql import text


_test_users = [
    {
        'uid': '2040',
        'deleted_at': None,
    },
    {
        'uid': '1022796',
        'deleted_at': utc_now(),
    },
]


def clear():
    with open(app.config['BASE_DIR'] + '/scripts/db/drop_schema.sql', 'r') as ddlfile:
        db.session().execute(text(ddlfile.read()))
        std_commit()


def load(create_test_data=True):
    cache.clear()
    _load_schemas()
    if create_test_data:
        _create_email_templates()
        _create_emails_sent()
        _create_users()
        _cache_externals()
        _run_jobs()
        _set_room_capability()
    return db


def _cache_externals():
    for external in ('calnet', 'canvas', 'kaltura'):
        for path in glob.glob(f'{BASE_DIR}/fixtures/{external}/*.json'):
            with open(path, 'r') as file:
                key = path.split('/')[-1].split('.')[0]
                cache.set(f'{external}/{key}', json.loads(file.read()))


def _load_schemas():
    """Create DB schema from SQL file."""
    with open(app.config['BASE_DIR'] + '/scripts/db/schema.sql', 'r') as ddlfile:
        db.session().execute(text(ddlfile.read()))
        std_commit()


def _create_email_templates():
    EmailTemplate.create(
        template_type='admin_alert_instructor_change',
        name='Alert admin instructor approval needed',
        subject_line='Instructor approval needed',
        message='<code>course.name</code> has new instructor(s).',
    )
    EmailTemplate.create(
        template_type='admin_alert_room_change',
        name='Alert admin when room change',
        subject_line='Room change alert',
        message='<code>course.name</code> has changed to a new room: <code>course.room</code>',
    )
    EmailTemplate.create(
        template_type='notify_instructor_of_changes',
        name='I\'m the Devil. Now kindly undo these straps.',
        subject_line='If you\'re the Devil, why not make the straps disappear?',
        message='That\'s much too vulgar a display of power.',
    )
    EmailTemplate.create(
        template_type='invitation',
        name='What an excellent day for an exorcism.',
        subject_line='You would like that?',
        message='Intensely.',
    )
    EmailTemplate.create(
        template_type='recordings_scheduled',
        name='Recordings scheduled',
        subject_line='Course scheduled for Course Capture',
        message='Recordings of type <code>recording.type</code> will be published to <code>publish.type</code>.',
    )
    std_commit(allow_test_environment=True)


def _create_emails_sent():
    term_id = app.config['CURRENT_TERM_ID']
    SentEmail.create(
        recipient_uids=['8765432'],
        section_id='28165',
        template_type='invitation',
        term_id=term_id,
    )
    std_commit(allow_test_environment=True)


def _create_users():
    for test_user in _test_users:
        user = AdminUser(uid=test_user['uid'])
        db.session.add(user)
        if test_user['deleted_at']:
            AdminUser.delete(user.uid)
    std_commit(allow_test_environment=True)


def _run_jobs():
    CanvasJob(app_context=app.app_context).run()
    DataLochSyncJob(app_context=app.app_context).run()
    UpdateRoomsJob(app_context=app.app_context).run()
    std_commit(allow_test_environment=True)


def _set_room_capability():
    for room in Room.all_rooms():
        if room.location in ['Barrows 106', 'Barker 101']:
            Room.update_capability(room.id, 'screencast')
        elif room.location in ['Li Ka Shing 145']:
            Room.set_auditorium(room.id, True)
            Room.update_capability(room.id, 'screencast_and_video')
    std_commit(allow_test_environment=True)


if __name__ == '__main__':
    import diablo.factory
    diablo.factory.create_app()
    load()
