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
from diablo.jobs.base_job import BaseJob
from diablo.jobs.tasks.admin_emails_task import AdminEmailsTask
from diablo.jobs.tasks.instructor_emails_task import InstructorEmailsTask
from diablo.jobs.tasks.invitation_emails_task import InvitationEmailsTask
from diablo.jobs.tasks.queued_emails_task import QueuedEmailsTask


class EmailsJob(BaseJob):

    def _run(self):
        # Why do we run QueuedEmailsTask twice? Answer: reduce risk of duplicate emails.
        # If this job crashes or gets stuck on the initial QueuedEmailsTask then nothing else happens.
        tasks = [
            QueuedEmailsTask(),
            AdminEmailsTask(),
            InstructorEmailsTask(),
            InvitationEmailsTask(),
            QueuedEmailsTask(),
        ]
        for task in tasks:
            task.run()

    @classmethod
    def description(cls):
        return f"""
            <ol>
                <li>{QueuedEmailsTask.description()}</li>
                <li>{AdminEmailsTask.description()}</li>
                <li>{InstructorEmailsTask.description()}</li>
                <li>{InvitationEmailsTask.description()}</li>
                <li>{QueuedEmailsTask.description()}</li>
            </ol>
        """

    @classmethod
    def key(cls):
        return 'emails'
