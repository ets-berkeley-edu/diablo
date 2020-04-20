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

import json


def api_approve(
        client,
        publish_type,
        recording_type,
        section_id,
        expected_status_code=200,
):
    response = client.post(
        '/api/course/approve',
        data=json.dumps({
            'publishType': publish_type,
            'recordingType': recording_type,
            'sectionId': section_id,
        }),
        content_type='application/json',
    )
    assert response.status_code == expected_status_code, f"""
        Expected status code: {expected_status_code}
        Actual status code: {response.status_code}
    """
    return response.json


def api_get_course(client, term_id, section_id, expected_status_code=200):
    response = client.get(f'/api/course/{term_id}/{section_id}')
    assert response.status_code == expected_status_code, f"""
        Expected status code: {expected_status_code}
        Actual status code: {response.status_code}
    """
    return response.json
