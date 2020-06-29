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
from datetime import datetime

from diablo.jobs.base_job import BaseJob
from diablo.jobs.errors import BackgroundJobError
from diablo.lib.berkeley import get_recording_end_date, get_recording_start_date
from diablo.lib.interpolator import interpolate_content
from diablo.merged.emailer import get_admin_alert_recipient
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import QueuedEmail
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app


class AdminEmailsJob(BaseJob):

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
        template_types = [
            'admin_alert_date_change',
            'admin_alert_instructor_change',
            'admin_alert_multiple_meeting_patterns',
            'admin_alert_room_change',
        ]
        return f"""
            Queues up admin notifications. Email templates used:
            <ul>
                {''.join(f'<li>{names_by_type.get(template_type)}</li>' for template_type in template_types)}
            </ul>
        """

    @classmethod
    def key(cls):
        return 'admin_emails'

    def _already_notified(self, section_ids, template_type):
        emails_sent = SentEmail.get_emails_of_type(
            section_ids=section_ids,
            template_type=template_type,
            term_id=self.term_id,
        )
        skip_section_ids = [email_sent.section_id for email_sent in emails_sent]
        skip_section_ids += QueuedEmail.get_all_section_ids(template_type=template_type, term_id=self.term_id)
        return skip_section_ids

    def _date_change_alerts(self):
        template_type = 'admin_alert_date_change'
        scheduled = Scheduled.get_all_scheduled(self.term_id)
        exclude_section_ids = self._already_notified(
            section_ids=[s.section_id for s in scheduled],
            template_type=template_type,
        )
        scheduled_subset = [s for s in scheduled if s.section_id not in exclude_section_ids]
        courses = SisSection.get_courses(
            section_ids=[s.section_id for s in scheduled_subset],
            term_id=self.term_id,
        )
        courses_by_section_id = dict((course['sectionId'], course) for course in courses)

        for scheduled in scheduled_subset:
            course = courses_by_section_id[scheduled.section_id]
            meetings = course.get('meetings', {}).get('eligible', [])
            if len(meetings):
                api_json = scheduled.to_api_json()
                expected_start_date = get_recording_start_date(meetings[0])
                expected_end_date = get_recording_end_date(meetings[0])

                def _format(date):
                    return datetime.strftime(date, '%Y-%m-%d')
                start_date_mismatch = _format(expected_start_date) != api_json['meetingStartDate']
                if start_date_mismatch or _format(expected_end_date) != api_json['meetingEndDate']:
                    self._notify(course=course, template_type=template_type)

    def _instructor_change_alerts(self):
        for course in self.courses:
            if course['scheduled'] and course['scheduled']['hasObsoleteInstructors']:
                self._notify(course=course, template_type='admin_alert_instructor_change')

    def _multiple_meeting_pattern_alerts(self):
        template_type = 'admin_alert_multiple_meeting_patterns'
        courses = SisSection.get_courses_scheduled_nonstandard_dates(self.term_id)
        # Skip the already-notified courses
        already_notified = self._already_notified([course['sectionId'] for course in courses], template_type)
        for course in list(filter(lambda c: c['sectionId'] not in already_notified, courses)):
            self._notify(course=course, template_type=template_type)

    def _room_change_alerts(self):
        for course in self.courses:
            if course['scheduled'] and course['scheduled']['hasObsoleteRoom']:
                self._notify(course=course, template_type='admin_alert_room_change')

    def _notify(self, course, template_type):
        email_template = EmailTemplate.get_template_by_type(template_type)
        if email_template:
            recipient = get_admin_alert_recipient()
            message = interpolate_content(
                templated_string=email_template.message,
                course=course,
                recipient_name=recipient['name'],
            )
            subject_line = interpolate_content(
                templated_string=email_template.subject_line,
                course=course,
                recipient_name=recipient['name'],
            )
            QueuedEmail.create(
                message=message,
                subject_line=subject_line,
                recipient=recipient,
                section_id=course['sectionId'],
                template_type=template_type,
                term_id=self.term_id,
            )
        else:
            raise BackgroundJobError(f"""
                No email template of type {template_type} is available.
                Diablo admin NOT notified in regard to course {course['label']}.
            """)
