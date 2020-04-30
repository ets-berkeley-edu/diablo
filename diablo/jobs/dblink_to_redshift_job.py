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
from itertools import islice

from diablo import db, std_commit
from diablo.externals.rds import execute
from diablo.jobs.background_job_manager import BackgroundJobError
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import insert_or_update_instructors, refresh_rooms
from diablo.lib.db import resolve_sql_template
from diablo.models.cross_listing import CrossListing
from diablo.models.sis_section import SisSection
from flask import current_app as app
from sqlalchemy import text


class DblinkToRedshiftJob(BaseJob):

    def run(self, args=None):
        resolved_ddl_rds = resolve_sql_template('update_rds_sis_sections.template.sql')
        if execute(resolved_ddl_rds):
            term_id = app.config['CURRENT_TERM_ID']
            self.after_dblink_courses_refresh(term_id)
        else:
            raise BackgroundJobError('Failed to update RDS indexes for intermediate schema.')

    @classmethod
    def description(cls):
        return 'Get latest course, instructor and room data from the Data Lake.'

    @classmethod
    def after_dblink_courses_refresh(cls, term_id):
        distinct_instructor_uids = SisSection.get_distinct_instructor_uids()
        insert_or_update_instructors(distinct_instructor_uids)
        app.logger.info(f'{len(distinct_instructor_uids)} instructors updated')

        refresh_rooms()
        app.logger.info('RDS indexes updated.')

        # Populate 'cross_listings' table: If {123, 234, 345} is a set of cross-listed section_ids then:
        #  1. Section 123 will have a record in the 'sis_sections' table; 234 and 345 will not.
        #  2. The cross-listings table will get 123: [234, 345]
        #  3. We collapse the names of the three section into a single name/title for section 123

        # IMPORTANT: These will be ordered by schedule (time and location)
        sql = f"""
            SELECT
                section_id,
                trim(concat(
                    meeting_days,
                    meeting_end_date,
                    meeting_end_time,
                    meeting_location,
                    meeting_start_date,
                    meeting_start_time
                )) as schedule
            FROM sis_sections
            WHERE term_id = :term_id
                AND meeting_days <> ''
                AND meeting_end_date <> ''
                AND meeting_end_time <> ''
                AND meeting_location <> ''
                AND meeting_start_date <> ''
                AND meeting_start_time <> ''
            ORDER BY schedule, section_id
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        cross_listings = {}
        previous_schedule = None
        current_key = None

        for row in rows:
            section_id = row['section_id']
            schedule = row['schedule']
            if section_id not in cross_listings:
                if schedule != previous_schedule:
                    current_key = section_id
                    cross_listings[current_key] = []
                else:
                    cross_listings[current_key].append(section_id)
            previous_schedule = schedule

        # Toss out section_ids with no cross-listings
        for section_id, section_ids in cross_listings.copy().items():
            if not section_ids:
                cross_listings.pop(section_id)

        # Prepare for refresh by deleting old rows
        db.session.execute(CrossListing.__table__.delete().where(CrossListing.term_id == term_id))

        def chunks(data, chunk_size=500):
            iterator = iter(data)
            for i in range(0, len(data), chunk_size):
                yield {k: data[k] for k in islice(iterator, chunk_size)}

        delete_section_ids = []

        for cross_listings_chunk in chunks(cross_listings):
            cross_listing_count = len(cross_listings_chunk)
            query = 'INSERT INTO cross_listings (term_id, section_id, cross_listed_section_ids, created_at) VALUES'
            for index, (section_id, cross_listed_section_ids) in enumerate(cross_listings_chunk.items()):
                query += f' (:term_id, {section_id}, ' + "'{" + _join(cross_listed_section_ids, ', ') + "}', now())"
                if index < cross_listing_count - 1:
                    query += ','
                # Cross-referenced section ids will be deleted in  sis_sections table
                delete_section_ids.extend(cross_listed_section_ids)
            db.session.execute(query, {'term_id': term_id})

        # Cross-listed section_ids are "deleted" in sis_sections, represented in cross_listings table
        SisSection.delete_all(section_ids=delete_section_ids, term_id=term_id)

        std_commit()


def _join(items, separator=', '):
    return separator.join(str(item) for item in items)
