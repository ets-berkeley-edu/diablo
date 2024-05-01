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
from diablo.externals.rds import execute
from diablo.jobs.base_job import BaseJob
from diablo.jobs.errors import BackgroundJobError
from diablo.jobs.schedule_updates_job import _queue_schedule_updates
from diablo.jobs.util import insert_or_update_instructors, refresh_cross_listings, refresh_rooms
from diablo.lib.db import resolve_sql_template
from diablo.models.sis_section import SisSection
from flask import current_app as app


class SisDataRefreshJob(BaseJob):

    def _run(self, args=None):
        term_id = app.config['CURRENT_TERM_ID']
        refresh = execute(resolve_sql_template('update_rds_sis_sections.template.sql'))
        if refresh:
            self.after_sis_data_refresh(term_id)
            _queue_schedule_updates(term_id)
        else:
            raise BackgroundJobError('Failed to update SIS data from Nessie.')

    @classmethod
    def description(cls):
        return 'Get latest course, instructor and room data from the Data Lake.'

    @classmethod
    def key(cls):
        return 'sis_data_refresh'

    @classmethod
    def after_sis_data_refresh(cls, term_id):
        app.logger.info('Starting instructor update')
        distinct_instructor_uids = SisSection.get_distinct_instructor_uids()
        insert_or_update_instructors(distinct_instructor_uids)
        app.logger.info(f'{len(distinct_instructor_uids)} instructors updated')

        refresh_rooms()
        app.logger.info('RDS indexes updated.')

        refresh_cross_listings(term_id=term_id)
        app.logger.info('Cross-listings updated.')
