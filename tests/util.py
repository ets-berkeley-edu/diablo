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
from contextlib import contextmanager

from diablo import db, std_commit
from diablo.jobs.doomed_to_failure import DoomedToFailure  # noqa
from diablo.models.job import Job
from sqlalchemy import text


@contextmanager
def scheduled_job(job_key):
    """Temporarily enabled job."""
    all_jobs = Job.get_all(include_disabled=True)
    job = next((j for j in all_jobs if j.key == job_key))
    disabled = job.disabled
    schedule_type = job.job_schedule_type
    schedule_value = job.job_schedule_value
    try:
        yield job
    finally:
        if disabled is not job.disabled:
            Job.update_disabled(job_id=job.id, disable=True)
        if schedule_type != job.job_schedule_type or schedule_value != job.job_schedule_value:
            Job.update_schedule(job_id=job.id, schedule_type=schedule_type, schedule_value=schedule_value)
        std_commit(allow_test_environment=True)


@contextmanager
def override_config(app, key, value):
    """Temporarily override an app config value."""
    old_value = app.config[key]
    app.config[key] = value
    try:
        yield
    finally:
        app.config[key] = old_value


@contextmanager
def simply_yield():
    yield


@contextmanager
def test_scheduling_workflow(app):
    """Delete all schedules before and after test."""
    def _delete_all_schedules():
        db.session.execute(text('DELETE FROM course_preferences'))
        db.session.execute(text('DELETE FROM opt_outs'))
        db.session.execute(text('DELETE FROM schedule_updates'))
        db.session.execute(text('DELETE FROM scheduled'))
        db.session.execute(text('DELETE FROM queued_emails'))
        db.session.execute(text('DELETE FROM sent_emails'))

    try:
        _delete_all_schedules()
        yield
    finally:
        _delete_all_schedules()
