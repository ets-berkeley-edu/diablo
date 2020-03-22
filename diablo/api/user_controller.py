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
from diablo.api.errors import ResourceNotFoundError
from diablo.api.util import admin_required
from diablo.lib.http import tolerant_jsonify
from diablo.lib.util import items_per_keys
from diablo.merged.calnet import get_calnet_user_for_uid, get_calnet_users_for_uids
from diablo.merged.sis import get_sections
from diablo.models.approval import Approval
from diablo.models.scheduled import Scheduled
from flask import current_app as app
from flask_login import current_user


@app.route('/api/user/my_profile')
def my_profile():
    return tolerant_jsonify(current_user.to_api_json())


@app.route('/api/user/<uid>')
@admin_required
def get_user(uid):
    user = get_calnet_user_for_uid(app=app, uid=uid)
    if user.get('isExpiredPerLdap', True):
        raise ResourceNotFoundError('No such user')
    else:
        user['courses'] = get_sections(
            term_id=app.config['CURRENT_TERM_ID'],
            instructor_uid=uid,
        )
        _put_approvals_and_scheduled(user)
        return tolerant_jsonify(user)


def _put_approvals_and_scheduled(user):
    term_id = app.config['CURRENT_TERM_ID']
    section_ids = [course['sectionId'] for course in user['courses']]

    approvals = Approval.get_approvals_per_section_ids(section_ids=section_ids, term_id=term_id)
    approvals_per_section_id = items_per_keys(approvals, 'section_id')
    scheduled = Scheduled.get_scheduled_per_section_ids(section_ids=section_ids, term_id=term_id)
    scheduled_per_section_id = items_per_keys(scheduled, 'section_id')

    for course in user['courses']:
        _put_approvals_to_course(course, approvals, approvals_per_section_id)
        _put_items_to_course(course, 'scheduled', scheduled_per_section_id)


def _put_approvals_to_course(course, approvals, approvals_per_section_id):
    _put_items_to_course(course, 'approvals', approvals_per_section_id)
    approver_uids = [a['approvedByUid'] for a in course['approvals']]
    calnet_users = get_calnet_users_for_uids(app, approver_uids)
    for approval in course['approvals']:
        approval['approvedBy'] = calnet_users[approval['approvedByUid']]


def _put_items_to_course(course_, key, items_per_section_id):
    section_id_ = int(course_['sectionId'])
    if section_id_ in items_per_section_id:
        course_[key] = [item.to_api_json() for item in items_per_section_id[section_id_]]
    else:
        course_[key] = []
