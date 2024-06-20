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
from diablo.api.errors import ResourceNotFoundError
from diablo.api.util import admin_required
from diablo.externals.canvas import get_teaching_courses
from diablo.externals.loch import get_loch_basic_attributes_by_uid_or_email
from diablo.lib.http import tolerant_jsonify
from diablo.lib.util import basic_attributes_to_api_json
from diablo.merged.calnet import get_calnet_user_for_uid, get_calnet_users_for_uids
from diablo.models.admin_user import AdminUser
from diablo.models.sis_section import SisSection
from flask import current_app as app, request
from flask_login import current_user, login_required


@app.route('/api/user/my_profile')
def my_profile():
    profile = current_user.to_api_json(include_courses=True)
    return tolerant_jsonify(profile)


@app.route('/api/user/<uid>')
@admin_required
def get_user(uid):
    user = get_calnet_user_for_uid(app=app, uid=uid)
    if user.get('isExpiredPerLdap', True):
        raise ResourceNotFoundError('No such user')
    else:
        courses = SisSection.get_courses_per_instructor_uid(
            term_id=app.config['CURRENT_TERM_ID'],
            instructor_uid=uid,
        )
        user['courses'] = courses
        return tolerant_jsonify(user)


@app.route('/api/user/<uid>/calnet')
@login_required
def get_calnet_user(uid):
    return tolerant_jsonify(get_calnet_user_for_uid(app=app, uid=uid))


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
