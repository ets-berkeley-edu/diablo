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
from diablo import db, std_commit
from diablo.lib.util import utc_now
from diablo.models.base import Base
from sqlalchemy import and_


class Note(Base):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    term_id = db.Column(db.Integer)
    section_id = db.Column(db.Integer)
    uid = db.Column(db.String(80))
    body = db.Column(db.Text, nullable=False)
    deleted_at = db.Column(db.DateTime)

    def __init__(self, body, term_id=None, section_id=None, uid=None):
        self.term_id = term_id
        self.section_id = section_id
        self.uid = uid
        self.body = body

    def __repr__(self):
        return f"""<Note
                    id={self.id},
                    term_id={self.term_id},
                    section_id={self.section_id},
                    uid={self.uid},
                    body={self.body},
                    created_at={self.created_at},
                    updated_at={self.updated_at},
                    deleted_at={self.deleted_at}>
                """

    @classmethod
    def create_or_update(cls, body, term_id=None, section_id=None, uid=None):
        note = None
        if uid:
            note = cls.query.filter_by(uid=uid).first()
        elif term_id and section_id:
            note = cls.query.filter_by(term_id=term_id, section_id=section_id).first()
        if note:
            note.body = body
            note.deleted_at = None
        else:
            note = cls(
                body=body,
                term_id=term_id,
                section_id=section_id,
                uid=uid,
            )
        db.session.add(note)
        std_commit()
        return note

    @classmethod
    def delete(cls, term_id=None, section_id=None, uid=None):
        now = utc_now()
        note = None
        if uid:
            note = cls.query.filter_by(uid=uid).first()
        elif term_id and section_id:
            note = cls.query.filter_by(term_id=term_id, section_id=section_id).first()
        if note:
            note.deleted_at = now
        std_commit()
        return note

    @classmethod
    def get_note_for_uid(cls, uid):
        return cls.query.filter_by(uid=uid, deleted_at=None).first()

    @classmethod
    def get_notes_for_section_ids(cls, section_ids, term_id):
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id, cls.deleted_at == None)  # noqa: E711
        return cls.query.filter(criteria).order_by(cls.created_at).all()
