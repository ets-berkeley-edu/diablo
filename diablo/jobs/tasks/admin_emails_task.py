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
from diablo.jobs.tasks.base_task import BaseTask
from diablo.lib.berkeley import are_scheduled_dates_obsolete, are_scheduled_times_obsolete
from diablo.lib.interpolator import interpolate_content
from diablo.merged.emailer import get_admin_alert_recipient, send_system_error_email
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import QueuedEmail
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class AdminEmailsTask(BaseTask):

    def _run(self):
        self.term_id = app.config['CURRENT_TERM_ID']
        self.courses = SisSection.get_course_changes(term_id=self.term_id)
        self._date_change_alerts()
        self._instructor_change_alerts()
        self._multiple_meeting_pattern_alerts()
        self._room_change_alerts()

    @classmethod
    def description(cls):
        names_by_type = EmailTemplate.get_template_type_options()
        template_names = ', '.join(names_by_type.get(template_type) for template_type in [
            'admin_alert_date_change',
            'admin_alert_instructor_change',
            'admin_alert_multiple_meeting_patterns',
            'admin_alert_room_change',
        ])
        return f'Queues up admin notifications. Email templates used: {template_names}'

    def _date_change_alerts(self):
        template_type = 'admin_alert_date_change'
        for course in self._get_courses_except_notified(template_type):
            meetings = course.get('meetings', {}).get('eligible', [])
            if len(meetings):
                meeting = meetings[0]
                scheduled = course['scheduled']
                obsolete_dates = are_scheduled_dates_obsolete(meeting=meeting, scheduled=scheduled)
                if obsolete_dates or are_scheduled_times_obsolete(meeting=meeting, scheduled=scheduled):
                    self._notify(course=course, template_type=template_type)

    def _instructor_change_alerts(self):
        template_type = 'admin_alert_instructor_change'
        for course in self._get_courses_except_notified(template_type):
            if course and course['scheduled']['hasObsoleteInstructors']:
                self._notify(course=course, template_type=template_type)

    def _multiple_meeting_pattern_alerts(self):
        template_type = 'admin_alert_multiple_meeting_patterns'
        for course in SisSection.get_courses_scheduled_nonstandard_dates(term_id=self.term_id):
            if template_type not in course['scheduled']['alerts']:
                self._notify(course=course, template_type=template_type)

    def _room_change_alerts(self):
        template_type = 'admin_alert_room_change'
        for course in self._get_courses_except_notified(template_type):
            if course['scheduled']['hasObsoleteRoom'] or course['deletedAt']:
                self._notify(course=course, template_type=template_type)

    def _notify(self, course, template_type):
        email_template = EmailTemplate.get_template_by_type(template_type)
        if email_template:
            def _get_interpolate_content(template):
                scheduled = course.get('scheduled', {})
                return interpolate_content(
                    course=course,
                    publish_type_name=scheduled.get('publishTypeName'),
                    recipient_name=recipient['name'],
                    recording_type_name=scheduled.get('recordingTypeName'),
                    templated_string=template,
                )
            recipient = get_admin_alert_recipient()
            QueuedEmail.create(
                message=_get_interpolate_content(email_template.message),
                recipient=recipient,
                section_id=course['sectionId'],
                subject_line=_get_interpolate_content(email_template.subject_line),
                template_type=template_type,
                term_id=self.term_id,
            )
            Scheduled.add_alert(scheduled_id=course['scheduled']['id'], template_type=template_type)
        else:
            send_system_error_email(f"""
                No email template of type {template_type} is available.
                Diablo admin NOT notified in regard to course {course['label']}.
            """)

    def _get_courses_except_notified(self, template_type):
        return list(filter(lambda c: template_type not in c['scheduled']['alerts'], self.courses))
