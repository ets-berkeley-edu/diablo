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

from diablo import db, std_commit
from sqlalchemy.dialects.postgresql import ARRAY


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    location = db.Column(db.String(255), nullable=False, unique=True)
    capabilities = db.Column(ARRAY(db.String(255)), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            location,
            capabilities,
    ):
        self.location = location
        self.capabilities = capabilities

    def __repr__(self):
        return f"""<Room
                    id={self.id},
                    location={self.location},
                    capabilities={self.capabilities},
                    created_at={self.created_at}>
                """

    @classmethod
    def create_or_update(cls, location, capabilities):
        room = cls.query.filter_by(location=location).first()
        if room:
            room.capabilities = capabilities
        else:
            room = cls(location=location, capabilities=capabilities)
        db.session.add(room)
        std_commit()
        return room
