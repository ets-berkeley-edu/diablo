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
from diablo.lib.util import localize_datetime, to_isoformat
from diablo.models.base import Base


class Blackout(Base):
    __tablename__ = 'blackouts'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    name = db.Column(db.String(255), nullable=False, unique=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return f"""<Blackout id={self.id},
                    name={self.name},
                    start_date={to_isoformat(self.start_date)},
                    end_date={to_isoformat(self.end_date)},
                """

    @classmethod
    def create(cls, name, start_date, end_date):
        blackout = cls(
            name=name,
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(blackout)
        std_commit()
        return blackout

    @classmethod
    def delete_blackout(cls, blackout_id):
        db.session.delete(cls.query.filter_by(id=blackout_id).first())
        std_commit()

    @classmethod
    def get_blackout(cls, blackout_id):
        return cls.query.filter_by(id=blackout_id).first()

    @classmethod
    def get_all_blackouts_names(cls):
        return cls.query.with_entities(cls.id, cls.name).order_by(cls.name).all()

    @classmethod
    def all_blackouts(cls):
        return cls.query.order_by().all()

    @classmethod
    def update(cls, blackout_id, name, start_date, end_date):
        blackout = cls.query.filter_by(id=blackout_id).first()
        blackout.name = name
        blackout.start_date = start_date
        blackout.end_date = end_date
        db.session.add(blackout)
        std_commit()
        return blackout

    def to_api_json(self):
        def _format(date):
            return localize_datetime(date).strftime('%Y-%m-%d')
        return {
            'id': self.id,
            'name': self.name,
            'startDate': _format(self.start_date),
            'endDate': _format(self.end_date),
            'createdAt': to_isoformat(self.created_at),
            'updatedAt': to_isoformat(self.updated_at),
        }
