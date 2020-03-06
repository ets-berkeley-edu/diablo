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

from diablo.api.errors import ForbiddenRequestError, ResourceNotFoundError
from diablo.lib.http import tolerant_jsonify
from diablo.merged.sis import get_section
from diablo.models.sign_up import SignUp
from flask import current_app as app
from flask_login import current_user, login_required


@app.route('/api/sign_up/status/<term_id>/<section_id>')
@login_required
def sign_up_status(term_id, section_id):
    section = get_section(term_id, section_id)
    if not section:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')
    instructor_uids = [i['uid'] for i in section['instructors']]
    if not current_user.is_admin and current_user.get_uid() not in instructor_uids:
        raise ForbiddenRequestError('Sorry, this request is unauthorized.')

    sign_up = SignUp.get_sign_up(term_id, section_id)
    if sign_up:
        status = sign_up.to_api_json()
        status.pop('sectionId')
        status.pop('termId')
    else:
        status = None
    return tolerant_jsonify({
        'termId': term_id,
        'section': section,
        'signUpStatus': status,
    })
