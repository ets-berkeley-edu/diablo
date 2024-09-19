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
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import get_eligible_courses, remove_blackout_events, schedule_recordings
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import announce_semester_start
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES
from flask import current_app as app


class SemesterStartJob(BaseJob):

    def _run(self):
        term_id = app.config['CURRENT_TERM_ID']
        courses = get_eligible_courses(term_id)
        app.logger.info(f'Preparing to schedule recordings for {len(courses)} eligible courses.')
        courses_by_instructor_uid = {}

        # Schedule recordings
        for course in courses:
            if not course['scheduled'] and not course['hasOptedOut']:
                scheduled = schedule_recordings(course)
                course['scheduled'] = [s.to_api_json() for s in scheduled]
            for instructor in list(filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES, course['instructors'])):
                if instructor['uid'] not in courses_by_instructor_uid:
                    courses_by_instructor_uid[instructor['uid']] = {'instructor': instructor, 'courses': []}
                courses_by_instructor_uid[instructor['uid']]['courses'].append(course)

        remove_blackout_events()

        # Queue semester start emails
        for uid, instructor_courses in courses_by_instructor_uid.items():
            announce_semester_start(instructor_courses['instructor'], instructor_courses['courses'])

    @classmethod
    def description(cls):
        return f"""
            This job is intended to be run once, manually, at the start of each term. It:
            <ul>
                <li>Schedules initial recordings via Kaltura API</li>
                <li>Queues up '{EmailTemplate.get_template_type_options()['semester_start']}' emails</li>
            </ul>
        """

    @classmethod
    def key(cls):
        return 'semester_start'
