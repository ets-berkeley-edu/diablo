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
from diablo.api.util import admin_required
from diablo.lib.http import tolerant_jsonify
from diablo.merged.sis import get_courses_per_section_ids
from diablo.models.approval import Approval
from diablo.models.scheduled import Scheduled
from flask import current_app as app


@app.route('/api/report/term/<term_id>')
@admin_required
def term_report(term_id):
    def _objects_per_section_id(objects):
        per_section_id = {}
        for obj in objects:
            key = str(obj.section_id)
            if obj.section_id not in per_section_id:
                per_section_id[key] = []
            per_section_id[key].append(obj.to_api_json())
        return per_section_id

    api_json = []
    approvals_per_section_id = _objects_per_section_id(Approval.get_approvals_per_term(term_id))
    scheduled_per_section_id = _objects_per_section_id(Scheduled.get_all_scheduled(term_id))
    section_ids = set(approvals_per_section_id.keys()).union(set(scheduled_per_section_id.keys()))

    for section in get_courses_per_section_ids(term_id, section_ids):
        section_id = section['sectionId']
        section['approvals'] = approvals_per_section_id.get(section_id, [])
        section['scheduled'] = scheduled_per_section_id.get(section_id, [])
        api_json.append(section)
    return tolerant_jsonify(api_json)
