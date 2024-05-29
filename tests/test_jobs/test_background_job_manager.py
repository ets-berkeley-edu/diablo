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

from diablo import std_commit
from diablo.factory import background_job_manager
from diablo.jobs.doomed_to_failure import DoomedToFailure
from diablo.jobs.emails_job import EmailsJob
from diablo.models.job import Job
from diablo.models.sent_email import SentEmail
from tests.util import simply_yield


class TestBackgroundJobManager:

    def test_started_at_property(self):
        """The started_at property is only defined when background_job_manager is running."""
        assert background_job_manager.is_running()
        original_started_at = background_job_manager.get_started_at()
        assert original_started_at

        background_job_manager.restart()
        assert original_started_at != background_job_manager.get_started_at()
        assert background_job_manager.is_running()

    def test_alert_on_job_failure(self, app):
        def _get_admin_email_count():
            return len(SentEmail.get_emails_sent_to(uid=app.config['EMAIL_DIABLO_ADMIN_UID']))

        email_count = _get_admin_email_count()
        # No alert on happy job.
        EmailsJob(simply_yield).run()
        assert _get_admin_email_count() == email_count
        # Alert on sad job.
        all_jobs = Job.get_all(include_disabled=True)
        doomed_job = next((j for j in all_jobs if j.key == DoomedToFailure.key()))

        # Make sure job is enabled
        Job.update_disabled(job_id=doomed_job.id, disable=False)
        std_commit(allow_test_environment=True)
        DoomedToFailure(simply_yield).run()
        # Failure alerts do not go through the queue.
        assert _get_admin_email_count() == email_count + 1
