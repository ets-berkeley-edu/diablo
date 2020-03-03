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

from diablo.merged import calnet
from diablo.models.authorized_user import AuthorizedUser
from flask import current_app as app
from flask_login import UserMixin


class UserSession(UserMixin):

    def __init__(self, user_id=None):
        try:
            # Type 'int' is required for user_id
            self.user_id = int(user_id) if user_id else None
        except ValueError:
            self.user_id = None
        if self.user_id:
            self.api_json = self.load_user(self.user_id)
        else:
            self.api_json = self._get_api_json()

    def get_id(self):
        return self.user_id

    def get_uid(self):
        return self.api_json['uid']

    @property
    def is_active(self):
        return self.api_json['isActive']

    @property
    def is_authenticated(self):
        return self.api_json['isAuthenticated']

    @property
    def is_anonymous(self):
        return not self.api_json['isAnonymous']

    @property
    def is_admin(self):
        return self.api_json['isAdmin']

    def to_api_json(self):
        return self.api_json

    @classmethod
    def load_user(cls, user_id):
        return cls._get_api_json(user=AuthorizedUser.find_by_id(user_id))

    @classmethod
    def _get_api_json(cls, user=None):
        calnet_profile = calnet.get_calnet_user_for_uid(app, user.uid) if user else None
        is_active = bool(calnet_profile)
        return {
            **(calnet_profile or {}),
            **{
                'id': user and user.id,
                'isActive': is_active,
                'isAdmin': user and user.is_admin,
                'isAnonymous': not is_active,
                'isAuthenticated': is_active,
                'uid': user and user.uid,
            },
        }
