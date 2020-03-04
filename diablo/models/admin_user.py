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

from diablo import db
from diablo.models.base import Base
from sqlalchemy import text


class AdminUser(Base):
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    uid = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, uid):
        self.uid = uid

    def __repr__(self):
        return f"""<AdminUser
                    uid={self.uid},
                    created_at={self.created_at},
                    updated_at={self.updated_at}>
                """

    @classmethod
    def is_admin(cls, uid):
        return cls.query.filter_by(uid=uid).first() is not None

    @classmethod
    def get_id_per_uid(cls, uid):
        query = text('SELECT id FROM admin_users WHERE uid = :uid')
        result = db.session.execute(query, {'uid': uid}).first()
        return result and result['id']
