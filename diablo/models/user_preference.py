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

from diablo import db, std_commit
from diablo.lib.util import to_isoformat, utc_now


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'

    uid = db.Column(db.String(255), primary_key=True)
    do_not_email = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def __init__(
            self,
            uid,
            do_not_email=False,
    ):
        self.uid = uid
        self.do_not_email = do_not_email

    def __repr__(self):
        return f"""<UserPreferences
                    uid={self.uid},
                    do_not_email={self.do_not_email},
                """

    @classmethod
    def get_user_preferences(cls, uid):
        return cls.query.filter_by(uid=uid).first()

    @classmethod
    def update_do_not_email(
            cls,
            uid,
            do_not_email,
    ):
        preferences = cls.get_user_preferences(uid)
        if preferences:
            preferences.do_not_email = do_not_email
        else:
            preferences = cls(
                uid=uid,
                do_not_email=do_not_email,
            )
        db.session.add(preferences)
        std_commit()
        return preferences

    def to_api_json(self):
        feed = {
            'uid': self.uid,
            'doNotEmail': self.do_not_email,
            'createdAt': to_isoformat(self.created_at),
        }
        return feed
