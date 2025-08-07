"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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
import traceback

from flask import current_app as app

from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.merged.emailer import send_system_error_email


class DeleteZoomRecordingsJob(BaseJob):

    def _run(self):
        kaltura = Kaltura()
        base_entries = kaltura.get_base_entries_for_owner(app.config['DEFAULT_ZOOM_USER_ID'])
        if len(base_entries):
            app.logger.info(f'Preparing to delete {len(base_entries)} Zoom recordings from dummy Kaltura account.')
            for entry in base_entries:
                try:
                    kaltura.delete_base_entry(entry.id)
                except Exception as e:
                    summary = f'Failed to delete Zoom recording from dummy Kaltura account (base entry id {entry.id})'
                    app.logger.error(summary)
                    app.logger.exception(e)
                    send_system_error_email(
                        message=f'{summary}\n\n<pre>{traceback.format_exc()}</pre>',
                        subject=summary,
                    )
            app.logger.info('Recording deletion complete.')
        else:
            app.logger.info('No Zoom recordings found under dummy Kaltura account.')

    @classmethod
    def description(cls):
        return 'Delete Zoom recordings from dummy Kaltura account.'

    @classmethod
    def key(cls):
        return 'delete_zoom_recordings'
