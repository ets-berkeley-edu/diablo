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

import re

from diablo.merged.calnet import get_calnet_user_for_uid
from diablo.merged.email import interpolate_email_content
from diablo.merged.sis import get_section
from flask import current_app as app


class TestInterpolation:

    def test_interpolate_email_content(self):
        user = get_calnet_user_for_uid(app, '8765432')
        course = get_section(app.config['CURRENT_TERM_ID'], '28165')
        interpolated = interpolate_email_content(
            course=course,
            recipient_name=user['name'],
            templated_string=_get_email_template(),
            extra_key_value_pairs={
                'email.signature': '&copy; 2020 The Regents of the University of California',
            },
        )
        actual = _normalize(interpolated)
        expected = _normalize(_get_expected_email())
        assert expected == actual


def _get_expected_email():
    return """Hello William Peter Blatty,

    Your Spring 2020 course COMPSCI 61B, "Data Structures", is eligible for Course Capture. This course meets MO,WE,FR
    from 3:00 pm to 3:59 pm.

    Go to <a href="http://foo.berkeley.edu">https://diablo-TODO.berkeley.edu/approve/2202/28165</a> and sign up.

    Thank you.

    &copy; 2020 The Regents of the University of California"""


def _get_email_template():
    return f"""Hello <code> user.name </code>,

    Your <code>term.name</code> course <code>course.name</code>, "<code>course.title</code>", is eligible
    for Course Capture. This course meets <code>course.days</code> from <code>course.time.start</code> to <code>
    course.time.end</code>.

    Go to <a href="http://foo.berkeley.edu"><code> signup.url </code></a> and sign up.

    Thank you.

    <code>email.signature</code>"""


def _normalize(message):
    return re.sub('[ ]+', ' ', re.sub('\n', ' ', message))
