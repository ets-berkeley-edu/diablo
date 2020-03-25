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
from diablo.merged.sis import get_courses_per_instructor
from diablo.models.admin_user import AdminUser
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
        self.api_json = self._get_api_json(self.uid)

    def get_id(self):
        # Type 'int' is required for Flask-login user_id
        return int(self.uid)

    def get_uid(self):
        return self.uid

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
        return cls._get_api_json(uid=user_id)

    @classmethod
    def _get_api_json(cls, uid=None):
        calnet_profile = None
        is_active = False
        is_admin = False
        courses = []
        if uid:
            calnet_profile = calnet.get_calnet_user_for_uid(app, uid)
            is_active = not calnet_profile.get('isExpiredPerLdap', True)
            if is_active:
                is_admin = AdminUser.is_admin(uid)
                courses = get_courses_per_instructor(
                    term_id=app.config['CURRENT_TERM_ID'],
                    instructor_uid=uid,
                )
                is_active = is_admin or bool(courses)
        return {
            **(calnet_profile or {}),
            **{
                'id': uid,
                'isActive': is_active,
                'isAdmin': is_admin,
                'isAnonymous': not is_active,
                'isAuthenticated': is_active,
                'isTeaching': bool(courses),
                'courses': courses,
                'uid': uid,
            },
        }
