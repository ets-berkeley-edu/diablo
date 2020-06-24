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

from diablo import cache, db, std_commit
from diablo.factory import background_job_manager
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.house_keeping_job import HouseKeepingJob
from diablo.jobs.sis_data_refresh_job import SisDataRefreshJob
from diablo.lib.development_db_utils import save_mock_courses
from diablo.lib.util import utc_now
from diablo.models.admin_user import AdminUser
from diablo.models.email_template import EmailTemplate
from diablo.models.job import Job
from diablo.models.room import Room
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy.sql import text
from tests.util import simply_yield

_test_users = [
    {
        'uid': '90001',
        'deleted_at': None,
    },
    {
        'uid': '90002',
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
        _load_courses()
        _set_up_and_run_jobs()
        _set_room_capability()
    return db


def _cache_externals():
    for external in ('calnet', 'canvas', 'kaltura'):
        for path in glob.glob(f"{app.config['FIXTURES_PATH']}/{external}/*.json"):
            with open(path, 'r') as file:
                key = path.split('/')[-1].split('.')[0]
                cache.set(f'{external}/{key}', json.loads(file.read()))


def _load_schemas():
    """Create DB schema from SQL file."""
    with open(app.config['BASE_DIR'] + '/scripts/db/schema.sql', 'r') as ddlfile:
        db.session().execute(text(ddlfile.read()))
        std_commit()


def _load_courses():
    term_id = app.config['CURRENT_TERM_ID']
    db.session.execute(SisSection.__table__.delete().where(SisSection.term_id == term_id))
    save_mock_courses(f"{app.config['FIXTURES_PATH']}/sis/courses.json")
    SisDataRefreshJob.after_sis_data_refresh(term_id=term_id)
    std_commit(allow_test_environment=True)


def _create_email_templates():
    EmailTemplate.create(
        template_type='admin_alert_date_change',
        name='Scheduled course had date change',
        subject_line='Funky dates!',
        message="""
            Scheduled recordings of <code>course.name</code> have invalid dates:
            <code>course.date.start</code> to <code>course.date.end</code>.
        """,
    )
    EmailTemplate.create(
        template_type='admin_alert_instructor_change',
        name='Alert admin instructors change',
        subject_line='Instructors have changed',
        message="""
            <code>course.name</code>:
            Old instructor(s) <code>instructors.previous</code>
            New instructor(s) <code>instructors.all</code>
        """,
    )
    EmailTemplate.create(
        template_type='admin_alert_multiple_meeting_patterns',
        name='Alert admin when multiple meeting patterns',
        subject_line="It's complicated!",
        message="""
            <code>course.name</code> has weird dates:
            <code>course.date.start</code> to <code>course.date.end</code>
        """,
    )
    EmailTemplate.create(
        template_type='admin_alert_room_change',
        name='Alert admin when room change',
        subject_line='Room change alert',
        message='<code>course.name</code> has changed to a new room: <code>course.room</code>',
    )
    EmailTemplate.create(
        template_type='notify_instructor_of_changes',
        name="I'm the Devil. Now kindly undo these straps.",
        subject_line="If you're the Devil, why not make the straps disappear?",
        message="That's much too vulgar a display of power.",
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
    EmailTemplate.create(
        template_type='waiting_for_approval',
        name='Waiting for approval',
        subject_line="Who's Captain Howdy?",
        message='You know, I make the questions and he does the answers.',
    )
    std_commit(allow_test_environment=True)


def _create_emails_sent():
    term_id = app.config['CURRENT_TERM_ID']
    SentEmail.create(
        recipient_uid='00001',
        section_id='50001',
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


def _set_up_and_run_jobs():
    Job.create(job_schedule_type='day_at', job_schedule_value='15:00', key='kaltura')
    Job.create(job_schedule_type='day_at', job_schedule_value='04:30', key='queued_emails')
    Job.create(job_schedule_type='day_at', job_schedule_value='22:00', key='house_keeping')
    Job.create(job_schedule_type='minutes', job_schedule_value='120', key='instructor_emails')
    Job.create(job_schedule_type='minutes', job_schedule_value='120', key='invitations')
    Job.create(disabled=True, job_schedule_type='minutes', job_schedule_value='120', key='admin_emails')
    Job.create(job_schedule_type='day_at', job_schedule_value='16:00', key='canvas')
    Job.create(disabled=True, job_schedule_type='minutes', job_schedule_value='5', key='doomed_to_fail')

    background_job_manager.start(app)
    HouseKeepingJob(app_context=simply_yield).run()
    CanvasJob(app_context=simply_yield).run()
    std_commit(allow_test_environment=True)


def _set_room_capability():
    for room in Room.all_rooms():
        if room.location in ['Barrows 106', 'Li Ka Shing 145']:
            Room.set_auditorium(room.id, True)

        if room.location == 'Barrows 106':
            Room.update_capability(room.id, 'screencast')
        elif room.location in ['Li Ka Shing 145', 'Barker 101']:
            Room.update_capability(room.id, 'screencast_and_video')
    std_commit(allow_test_environment=True)


if __name__ == '__main__':
    import diablo.factory
    diablo.factory.create_app()
    load()
