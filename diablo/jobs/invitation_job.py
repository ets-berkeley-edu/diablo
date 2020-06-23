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

from diablo.jobs.base_job import BaseJob
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import QueuedEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app


class InvitationJob(BaseJob):

    def _run(self):
        self.term_id = app.config['CURRENT_TERM_ID']
        self.email_new_invites()

    @classmethod
    def description(cls):
        names_by_type = EmailTemplate.get_template_type_options()
        template_types = ['invitation']
        return f"""
            Queues up instructor invitations. Email templates used:
            <ul>
                {''.join(f'<li>{names_by_type.get(template_type)}</li>' for template_type in template_types)}
            </ul>
            NOTE: The '{names_by_type['invitation']}' email is queued by the Kaltura job, when recordings are
            scheduled, and sent by the Queued Emails job.
        """

    @classmethod
    def key(cls):
        return 'invitations'

    def email_new_invites(self):
        for course in SisSection.get_courses(term_id=self.term_id):
            if not course['hasOptedOut'] and len(course.get('meetings', {}).get('eligible', [])) == 1:
                for i in course['instructors']:
                    if not i['wasSentInvite']:
                        QueuedEmail.create(
                            recipient=i,
                            section_id=course['sectionId'],
                            template_type='invitation',
                            term_id=self.term_id,
                        )
