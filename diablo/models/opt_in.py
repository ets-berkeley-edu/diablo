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
from sqlalchemy import and_, or_

from diablo import db, std_commit
from diablo.lib.util import to_isoformat, utc_now
from diablo.models.cross_listing import CrossListing


class OptIn(db.Model):
    __tablename__ = 'opt_ins'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    instructor_uid = db.Column(db.String, nullable=False)
    term_id = db.Column(db.Integer)
    section_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def __init__(
            self,
            instructor_uid,
            term_id=None,
            section_id=None,
    ):
        self.instructor_uid = instructor_uid
        self.term_id = term_id
        self.section_id = section_id

    def __repr__(self):
        return f"""<OptIn
                    instructor_uid={self.instructor_uid},
                    term_id={self.term_id},
                    section_id={self.section_id},
                    created_at={self.created_at}
                """

    @classmethod
    def get_all_opt_ins(cls, term_id):
        return cls.query.filter(or_(cls.term_id == term_id, cls.term_id == None)).all()  # noqa: E711

    @classmethod
    def get_blanket_opt_ins_for_uid(cls, uid):
        return cls.query.filter(and_(cls.instructor_uid == uid, cls.section_id == None)).all()  # noqa: E711

    @classmethod
    def get_opt_ins_for_instructor_uid(cls, instructor_uid, term_id):
        return cls.query.filter(and_(cls.instructor_uid == instructor_uid, or_(cls.term_id == term_id, cls.term_id == None))).all()  # noqa: E711

    @classmethod
    def get_opt_ins_for_section(cls, section_id=None, term_id=None):
        return cls.query.filter_by(section_id=section_id, term_id=term_id).all()

    @classmethod
    def update_opt_in(cls, instructor_uid, term_id, section_id, opt_in):
        if section_id is None:
            section_ids = [None]
            criteria = and_(cls.section_id == None, cls.term_id == term_id, cls.instructor_uid == instructor_uid)  # noqa: E711
        else:
            section_ids = _get_section_ids_with_xlistings(section_id, term_id)
            criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id, cls.instructor_uid == instructor_uid)

        if opt_in is False:
            cls.query.filter(criteria).delete()
        else:
            for row in cls.query.filter(criteria).all():
                if row.section_id in section_ids:
                    section_ids.remove(row.section_id)
            for section_id in section_ids:  # noqa: PLR1704
                opt_in = cls(
                    instructor_uid=instructor_uid,
                    term_id=term_id,
                    section_id=section_id,
                )
                db.session.add(opt_in)
        std_commit()
        return True

    def to_api_json(self):
        return {
            'instructorUid': self.instructor_uid,
            'termId': self.term_id,
            'sectionId': self.section_id,
            'createdAt': to_isoformat(self.created_at),
        }


def _get_section_ids_with_xlistings(section_id, term_id):
    return CrossListing.get_cross_listed_section_ids(section_id=section_id, term_id=term_id) + [section_id]
