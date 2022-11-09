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
import random

from diablo.jobs.util import get_instructors_who_can_edit_recordings
from diablo.lib.util import get_names_of_days, readable_join, utc_now


class TestUtils:

    def test_full_day_names(self):
        assert get_names_of_days([]) == []
        assert get_names_of_days(['mon', 'wed', 'fri']) == ['Monday', 'Wednesday', 'Friday']
        assert get_names_of_days(['TU', 'TH']) == ['Tuesday', 'Thursday']
        assert get_names_of_days(['Tuesday', 'Thursday', 'Payday']) == ['Tuesday', 'Thursday', None]

    def test_readable_join(self):
        assert readable_join(None) == ''
        assert readable_join([]) == ''
        assert readable_join(['Moe']) == 'Moe'
        assert readable_join(['Moe', 'Larry']) == 'Moe and Larry'
        assert readable_join(['Moe', 'Larry', 'Curly']) == 'Moe, Larry and Curly'

    def test_get_instructors_who_can_edit_recordings(self):
        def course(instructors, can_aprx_instructors_edit_recordings=False):
            return {
                'canAprxInstructorsEditRecordings': can_aprx_instructors_edit_recordings,
                'instructors': instructors,
            }

        def instructor(role_code, deleted_at=None):
            return {
                'deletedAt': deleted_at,
                'roleCode': role_code,
                'uid': random.randint(1, 99999),
            }
        aprx_instructor = instructor(role_code='APRX')
        deleted_instructor = instructor(role_code='PI', deleted_at=utc_now())
        teaching_instructor = instructor(role_code='PI')

        def _assert_who_can_edit_recordings(course_, instructors_expected):
            instructors_actual = get_instructors_who_can_edit_recordings(course_)
            actual_uids = [instructor['uid'] for instructor in instructors_actual]
            expected_uids = [instructor['uid'] for instructor in instructors_expected]
            assert set(actual_uids) == set(expected_uids)

        _assert_who_can_edit_recordings(
            course_=course([]),
            instructors_expected=[],
        )
        _assert_who_can_edit_recordings(
            course_=course(instructors=[teaching_instructor]),
            instructors_expected=[teaching_instructor],
        )
        _assert_who_can_edit_recordings(
            course_=course(instructors=[deleted_instructor, teaching_instructor]),
            instructors_expected=[teaching_instructor],
        )
        _assert_who_can_edit_recordings(
            course_=course(
                can_aprx_instructors_edit_recordings=True,
                instructors=[aprx_instructor, deleted_instructor, teaching_instructor],
            ),
            instructors_expected=[aprx_instructor, teaching_instructor],
        )
