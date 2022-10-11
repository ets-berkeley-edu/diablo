"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.models.cross_listing import CrossListing
from sqlalchemy import and_


class CoursePreference(db.Model):
    __tablename__ = 'course_preferences'

    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    has_opted_out = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, term_id, section_id, has_opted_out):
        self.term_id = term_id
        self.section_id = section_id
        self.has_opted_out = has_opted_out

    def __repr__(self):
        return f"""<CoursePreferences
                    term_id={self.term_id},
                    section_id={self.section_id},
                    has_opted_out={self.has_opted_out}
                    created_at={self.created_at}
                """

    @classmethod
    def get_section_ids_opted_out(cls, term_id):
        return [p.section_id for p in cls.query.filter_by(term_id=term_id, has_opted_out=True).all()]

    @classmethod
    def update_opt_out(cls, term_id, section_id, opt_out):
        section_ids = CrossListing.get_cross_listed_section_ids(section_id=section_id, term_id=term_id) + [section_id]
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        for row in cls.query.filter(criteria).all():
            row.has_opted_out = opt_out
            section_ids.remove(row.section_id)
        for section_id in section_ids:
            preferences = cls(
                term_id=term_id,
                section_id=section_id,
                has_opted_out=opt_out,
            )
            db.session.add(preferences)
        std_commit()
        return cls.query.filter_by(term_id=term_id, section_id=section_id).first()

    def to_api_json(self):
        return {
            'termId': self.term_id,
            'sectionId': self.section_id,
            'hasOptedOut': self.has_opted_out,
            'createdAt': to_isoformat(self.created_at),
        }
