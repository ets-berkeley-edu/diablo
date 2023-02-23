"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo.externals.canvas import get_canvas_course_sites, get_canvas_enrollment_term
from diablo.jobs.base_job import BaseJob
from diablo.merged.emailer import send_system_error_email
from diablo.models.canvas_course_site import CanvasCourseSite
from flask import current_app as app


class CanvasJob(BaseJob):

    def _run(self):
        sis_term_id = app.config['CURRENT_TERM_ID']
        canvas_enrollment_term = get_canvas_enrollment_term(sis_term_id)
        if canvas_enrollment_term:
            canvas_course_sites = get_canvas_course_sites(canvas_enrollment_term.id)
            if canvas_course_sites:
                CanvasCourseSite.refresh_term_data(
                    term_id=sis_term_id,
                    canvas_course_sites=canvas_course_sites,
                )
            else:
                send_system_error_email(
                    message='Please verify Canvas settings in Diablo config.',
                    subject=f'Canvas API call returned zero courses (canvas_term_id = {canvas_enrollment_term.id})',
                )
        else:
            send_system_error_email(
                message=f'No matching Canvas enrollment_term for sis_term_id = {sis_term_id}',
                subject=f'Canvas API returned no enrollment_term for sis_term_id = {sis_term_id}',
            )

    @classmethod
    def description(cls):
        return 'Collect canvas-course-site IDs from Canvas and insert them into Diablo db.'

    @classmethod
    def key(cls):
        return 'canvas'
