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
from diablo.externals.b_connected import BConnected
from diablo.jobs.base_job import BaseJob
from diablo.models.queued_email import QueuedEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app


class QueuedEmailsJob(BaseJob):

    def _run(self, args=None):
        term_id = app.config['CURRENT_TERM_ID']
        for queued_email in QueuedEmail.get_all(term_id):
            course = SisSection.get_course(term_id, queued_email.section_id)
            if not course:
                app.logger.warn(f'Email will remain queued until course data is present: {queued_email}')
                continue
            if course['hasOptedOut']:
                QueuedEmail.delete(queued_email)
                continue
            if BConnected().send(
                message=queued_email.message,
                recipient=queued_email.recipient,
                section_id=queued_email.section_id,
                subject_line=queued_email.subject_line,
                template_type=queued_email.template_type,
                term_id=term_id,
            ):
                QueuedEmail.delete(queued_email)
            else:
                # If send() fails then report the error and DO NOT delete the queued item.
                app.logger.error(f'Failed to send email: {queued_email}')

    @classmethod
    def description(cls):
        return 'Send all email that is queued.'

    @classmethod
    def key(cls):
        return 'queued_emails'
