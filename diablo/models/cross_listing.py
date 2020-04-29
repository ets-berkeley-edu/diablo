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
from datetime import datetime
from itertools import islice

from diablo import db, std_commit
from diablo.lib.util import to_isoformat
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ARRAY


class CrossListing(db.Model):
    __tablename__ = 'cross_listings'

    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    cross_listed_section_ids = db.Column(ARRAY(db.Integer), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            section_id,
            term_id,
            cross_listed_section_ids,
    ):
        self.section_id = section_id
        self.term_id = term_id
        self.cross_listed_section_ids = cross_listed_section_ids

    def __repr__(self):
        return f"""<CrossListing
                    section_id={self.section_id},
                    term_id={self.term_id},
                    cross_listed_section_ids={','.join(self.cross_listed_section_ids)},
                    created_at={self.created_at}>
                """

    @classmethod
    def create(
            cls,
            term_id,
            section_id,
            cross_listed_section_ids,
    ):
        approval = cls(
            section_id=section_id,
            term_id=term_id,
            cross_listed_section_ids=cross_listed_section_ids,
        )
        db.session.add(approval)
        std_commit()
        return approval

    @classmethod
    def get_cross_listed_sections(cls, section_id, term_id):
        row = cls.query.filter_by(section_id=section_id, term_id=term_id).first()
        return row.cross_listed_section_ids if row else []

    @classmethod
    def refresh(cls, term_id):
        # First group section IDs by schedule (time and location)
        sql = f"""
            SELECT
                section_id,
                trim(concat(meeting_days, meeting_end_date, meeting_end_time, meeting_location, meeting_start_date, meeting_start_time)) as schedule
            FROM sis_sections
            WHERE term_id = :term_id
                AND meeting_days <> ''
                AND meeting_end_date <> ''
                AND meeting_end_time <> ''
                AND meeting_location <> ''
                AND meeting_start_date <> ''
                AND meeting_start_time <> ''
        """
        rows = db.session.execute(
            text(sql),
            {
                'term_id': term_id,
            },
        )
        section_ids_per_schedule = {}
        for row in rows:
            schedule = row['schedule']
            if schedule not in section_ids_per_schedule:
                section_ids_per_schedule[schedule] = set()
            section_ids_per_schedule[schedule].add(row['section_id'])

        # Begin refresh by deleting existing rows per term_id
        db.session.execute(cls.__table__.delete().where(cls.term_id == term_id))

        # Next, populate 'cross_listings' table.
        # If section_ids (123, 234, 345) comprise a set of cross-listed section_ids then we construct:
        #   {
        #       123: [234, 345],
        #       234: [123, 345],
        #       345: [123, 234]
        #   }
        # The 'cross_listings' table will get the same three rows.

        cross_listings = {}
        for cross_listed_section_ids in list(section_ids_per_schedule.values()):
            if len(cross_listed_section_ids) > 1:
                for section_id in cross_listed_section_ids:
                    cross_listings[section_id] = [str(id_) for id_ in cross_listed_section_ids if id_ != section_id]

        def chunks(data, chunk_size=500):
            iterator = iter(data)
            for i in range(0, len(data), chunk_size):
                yield {k: data[k] for k in islice(iterator, chunk_size)}

        for cross_listings_chunk in chunks(cross_listings):
            cross_listing_count = len(cross_listings_chunk)
            query = 'INSERT INTO cross_listings (term_id, section_id, cross_listed_section_ids, created_at) VALUES'
            for index, (section_id, cross_listed_section_ids) in enumerate(cross_listings_chunk.items()):
                query += f' (:term_id, {section_id}, ' + "'{" + ', '.join(cross_listed_section_ids) + "}', now())"
                if index < cross_listing_count - 1:
                    query += ','
            db.session.execute(query, {'term_id': term_id})
            std_commit()

    def to_api_json(self):
        return {
            'sectionId': self.section_id,
            'termId': self.term_id,
            'crossListedSectionIds': self.cross_listed_section_ids,
            'createdAt': to_isoformat(self.created_at),
        }
