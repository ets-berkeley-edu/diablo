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

from diablo.externals.b_connected import BConnected
from diablo.jobs.base_job import BaseJob
from diablo.jobs.errors import BackgroundJobError
from diablo.merged.emailer import interpolate_email_content, send_course_related_email, send_system_error_email
from diablo.models.email_template import EmailTemplate
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class InstructorEmailsJob(BaseJob):

    def run(self):
        self.term_id = app.config['CURRENT_TERM_ID']
        self.email_new_invites()
        self.email_scheduled_courses()

    def email_new_invites(self):
        for course in SisSection.get_courses(term_id=self.term_id):
            if course['hasOptedOut']:
                next
            new_instructors = [i for i in course['instructors'] if not i['wasSentInvite']]
            if new_instructors:
                if not send_course_related_email(
                    course=course,
                    recipients=new_instructors,
                    template_type='invitation',
                    term_id=self.term_id,
                ):
                    app.logger.error(f"""
                        Failed to invite {len(new_instructors)} new instructors to section ID {course['sectionId']}).
                        Instructors: {new_instructors}""")

    def email_scheduled_courses(self):
        all_scheduled = Scheduled.get_all_scheduled(term_id=self.term_id)
        if not all_scheduled:
            return
        courses = SisSection.get_courses(term_id=self.term_id, section_ids=[s.section_id for s in all_scheduled])
        courses_per_section_id = dict((course['sectionId'], course) for course in courses)
        for scheduled in all_scheduled:
            course = courses_per_section_id[scheduled.section_id]
            if course:
                if scheduled.room_id != course['room']['id']:
                    template_type = 'room_change_no_longer_eligible'
                    email_template = EmailTemplate.get_template_by_type(template_type)
                    if email_template:
                        for instructor in course['instructors']:
                            BConnected().send(
                                message=interpolate_email_content(
                                    templated_string=email_template.message,
                                    course=course,
                                    instructor_name=instructor['name'],
                                    recipient_name=instructor['name'],
                                    recording_type_name=scheduled.recording_type,
                                ),
                                recipients=course['instructors'],
                                subject_line=interpolate_email_content(
                                    templated_string=email_template.subject_line,
                                    course=course,
                                    instructor_name=instructor['name'],
                                    recipient_name=instructor['name'],
                                    recording_type_name=scheduled.recording_type,
                                ),
                            )
                    else:
                        raise BackgroundJobError(f"""
                            No email template of type {template_type} is available.
                            {course['label']} instructors were NOT notified of scheduled: {scheduled}.
                        """)
            else:
                error = f'section_id of scheduled recordings was not found in SIS data: {scheduled}'
                app.logger.error(error)
                send_system_error_email(message=error)

    @classmethod
    def description(cls):
        return 'Notify instructors of room changes and similar.'

    @classmethod
    def key(cls):
        return 'instructor_emails'
