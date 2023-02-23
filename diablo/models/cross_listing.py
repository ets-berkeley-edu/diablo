"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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

from diablo import db, std_commit
from diablo.lib.util import to_isoformat
from sqlalchemy import and_, text
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
            cross_listed_section_ids,
            section_id,
            term_id,
    ):
        cross_listing = cls(
            cross_listed_section_ids=cross_listed_section_ids,
            section_id=section_id,
            term_id=term_id,
        )
        db.session.add(cross_listing)
        std_commit()
        return cross_listing

    @classmethod
    def get_instructor_uids_of_cross_listed_sections(cls, section_id, term_id):
        sql = """
            SELECT s.section_id, s.instructor_uid
            FROM cross_listings c
            JOIN sis_sections s ON s.section_id = ANY(c.cross_listed_section_ids::int[]) AND s.term_id = c.term_id
            WHERE c.section_id = :section_id AND c.term_id = :term_id AND s.instructor_uid IS NOT NULL
        """
        parameters = {
            'section_id': section_id,
            'term_id': term_id,
        }
        instruction_uids_by_section_id = {}
        for row in db.session.execute(text(sql), parameters):
            cross_listed_section_id = row['section_id']
            if cross_listed_section_id not in instruction_uids_by_section_id:
                instruction_uids_by_section_id[cross_listed_section_id] = []
            instructor_uid = row['instructor_uid']
            instruction_uids_by_section_id[cross_listed_section_id].append(instructor_uid)
        return instruction_uids_by_section_id

    @classmethod
    def get_cross_listed_section_ids(cls, section_id, term_id):
        row = cls.query.filter_by(section_id=section_id, term_id=term_id).first()
        return row.cross_listed_section_ids if row else []

    @classmethod
    def get_cross_listings_for_section_ids(cls, section_ids, term_id):
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        rows = cls.query.filter(criteria).all()
        return {row.section_id: row.cross_listed_section_ids for row in rows}

    def to_api_json(self):
        return {
            'sectionId': self.section_id,
            'termId': self.term_id,
            'crossListedSectionIds': self.cross_listed_section_ids,
            'createdAt': to_isoformat(self.created_at),
        }
