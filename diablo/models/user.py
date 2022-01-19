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
from diablo.merged.calnet import get_calnet_user_for_uid
from diablo.models.admin_user import AdminUser
from diablo.models.sis_section import SisSection
from flask import current_app as app
from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, uid=None):
        if uid:
            try:
                self.uid = str(int(uid))
            except ValueError:
                self.uid = None
        else:
            self.uid = None
        self.user = self._load_user(self.uid)

    def get_id(self):
        # Type 'int' is required for Flask-login user_id
        return int(self.uid)

    def uid(self):
        return self.uid

    @property
    def email_address(self):
        return self.user['emailAddress']

    @property
    def is_active(self):
        return self.user['isActive']

    @property
    def is_authenticated(self):
        return self.user['isAuthenticated']

    @property
    def is_anonymous(self):
        return not self.user['isAnonymous']

    @property
    def is_admin(self):
        return self.user['isAdmin']

    @property
    def is_teaching(self):
        return self.user['isTeaching']

    @classmethod
    def load_user(cls, user_id):
        return cls._load_user(uid=user_id)

    @property
    def name(self):
        return self.user['name']

    def to_api_json(self, include_courses=False):
        def _load_courses():
            return SisSection.get_courses_per_instructor_uid(
                term_id=app.config['CURRENT_TERM_ID'],
                instructor_uid=self.uid,
            )
        return {
            **self.user,
            **{
                'courses': _load_courses() if include_courses else [],
            },
        }

    @classmethod
    def _load_user(cls, uid=None):
        calnet_profile = get_calnet_user_for_uid(app, uid) if uid else {}
        expired = calnet_profile.get('isExpiredPerLdap', True)
        is_admin = not expired and AdminUser.is_admin(uid)
        is_teaching = not expired and SisSection.is_teaching(term_id=app.config['CURRENT_TERM_ID'], uid=uid)
        is_active = is_teaching or is_admin
        return {
            **calnet_profile,
            **{
                'id': uid,
                'emailAddress': calnet_profile.get('email'),
                'isActive': is_active,
                'isAdmin': is_admin,
                'isAnonymous': not is_active,
                'isAuthenticated': is_active,
                'isTeaching': is_teaching,
                'name': calnet_profile.get('name') or f'UID {uid}',
                'uid': uid,
            },
        }
