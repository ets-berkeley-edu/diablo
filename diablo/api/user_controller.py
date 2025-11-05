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
from flask import current_app as app
from flask import request
from flask_login import current_user, login_required

from diablo.api.errors import BadRequestError, ForbiddenRequestError, ResourceNotFoundError
from diablo.api.util import admin_required
from diablo.externals.canvas import get_teaching_courses
from diablo.externals.loch import get_loch_basic_attributes_by_uid_or_email
from diablo.lib.http_util import tolerant_jsonify
from diablo.lib.util import basic_attributes_to_api_json
from diablo.merged.calnet import get_calnet_user_for_uid, get_calnet_users_for_uids
from diablo.models.admin_user import AdminUser
from diablo.models.note import Note
from diablo.models.user import User
from diablo.models.user_preference import UserPreference


@app.route('/api/user/my_profile')
def my_profile():
    profile = current_user.to_api_json(include_courses=True)

    preferences = UserPreference.get_user_preferences(current_user.uid)
    profile['doNotEmail'] = preferences.do_not_email if preferences else False
    profile['optInNewCourses'] = preferences.opt_in_new_courses if preferences else False
    profile['prefersDarkMode'] = preferences.prefers_dark_mode if preferences else False

    return tolerant_jsonify(profile)


@app.route('/api/user/<uid>')
@admin_required
def get_user(uid):
    user = User(uid)
    if user.is_expired:
        raise ResourceNotFoundError('No such user')

    feed = user.to_api_json(include_courses=True)
    note = Note.get_note_for_uid(uid)
    if note:
        feed['note'] = note.body

    preferences = UserPreference.get_user_preferences(uid)
    feed['doNotEmail'] = preferences.do_not_email if preferences else False
    feed['optInNewCourses'] = preferences.opt_in_new_courses if preferences else False

    return tolerant_jsonify(feed)


@app.route('/api/user/<uid>/calnet')
@login_required
def get_calnet_user(uid):
    return tolerant_jsonify(get_calnet_user_for_uid(app=app, uid=uid))


@app.route('/api/user/<uid>/do_not_email/update', methods=['POST'])
@login_required
def update_do_not_email(uid):
    params = request.get_json()
    do_not_email = params.get('doNotEmail')

    if not uid or do_not_email is None:
        raise BadRequestError('Required params missing or invalid')

    if not current_user.is_admin and uid != current_user.uid:
        raise ForbiddenRequestError(f'Unauthorized to update user {uid}.')

    preferences = UserPreference.get_user_preferences(uid)
    if preferences and preferences.opt_in_new_courses:
        raise BadRequestError('Email preference cannot be changed while default opt-in is enabled.')

    preferences = UserPreference.update_do_not_email(uid, do_not_email)
    return tolerant_jsonify(preferences.to_api_json())


@app.route('/api/user/<uid>/opt_in_new_courses/update', methods=['POST'])
@login_required
def update_opt_in_new_courses(uid):
    params = request.get_json()
    opt_in_new_courses = params.get('optInNewCourses')

    if not uid or opt_in_new_courses is None:
        raise BadRequestError('Required params missing or invalid')

    if not current_user.is_admin and uid != current_user.uid:
        raise ForbiddenRequestError(f'Unauthorized to update user {uid}.')

    preferences = UserPreference.update_opt_in_new_courses(uid, opt_in_new_courses)
    return tolerant_jsonify(preferences.to_api_json())


@app.route('/api/user/prefers_dark_mode/update', methods=['POST'])
@login_required
def update_prefers_dark_mode():
    params = request.get_json()
    prefers_dark_mode = params.get('prefersDarkMode')

    if prefers_dark_mode is None:
        raise BadRequestError('Required param missing or invalid')

    preferences = UserPreference.update_prefers_dark_mode(current_user.uid, prefers_dark_mode)
    return tolerant_jsonify(preferences.to_api_json())


@app.route('/api/user/<uid>/note/delete', methods=['POST'])
@admin_required
def delete_user_note(uid):
    Note.delete(uid=uid)
    return tolerant_jsonify({'deleted': True})


@app.route('/api/user/<uid>/note/update', methods=['POST'])
@admin_required
def update_user_note(uid):
    params = request.get_json()
    body = params.get('body')
    if not body:
        raise BadRequestError('Required params missing or invalid')
    note = Note.create_or_update(body=body, uid=uid)
    return tolerant_jsonify({'note': note.body})


@app.route('/api/user/<uid>/teaching_sites')
@login_required
def get_user_teaching_sites(uid):
    return tolerant_jsonify(get_teaching_courses(uid=uid))


@app.route('/api/users/admins')
@admin_required
def admin_users():
    api_json = []
    admin_uids = [admin_user.uid for admin_user in AdminUser.all_admin_users()]
    for admin_user in get_calnet_users_for_uids(app=app, uids=admin_uids).values():
        api_json.append({
            'email': admin_user.get('email'),
            'name': admin_user.get('name'),
            'uid': admin_user['uid'],
        })
    return tolerant_jsonify(api_json)


@app.route('/api/users/search', methods=['POST'])
@login_required
def search_users():
    params = request.get_json()
    snippet = params.get('snippet').strip()
    attributes = get_loch_basic_attributes_by_uid_or_email(snippet, limit=20)
    results = [basic_attributes_to_api_json(a) for a in attributes]
    results.sort(key=lambda x: x['firstName'])
    return tolerant_jsonify(results)
