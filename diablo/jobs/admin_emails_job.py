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
from diablo.jobs.base_job import BaseJob
from diablo.jobs.errors import BackgroundJobError
from diablo.lib.interpolator import interpolate_content
from diablo.merged.emailer import get_admin_alert_recipients
from diablo.models.approval import Approval
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import QueuedEmail
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class AdminEmailsJob(BaseJob):

    def run(self):
        self.term_id = app.config['CURRENT_TERM_ID']
        self.all_scheduled = Scheduled.get_all_scheduled(term_id=self.term_id)
        if self.all_scheduled:
            self.courses = SisSection.get_courses(term_id=self.term_id, section_ids=[s.section_id for s in self.all_scheduled])
            self._alert_admin_of_instructor_changes()
            self._alert_admin_of_room_changes()

    @classmethod
    def description(cls):
        return 'Notify admins of relevant room and instructor changes.'

    @classmethod
    def key(cls):
        return 'admin_emails'

    def _alert_admin_of_instructor_changes(self):
        approval_uids_per_section_id = self._get_approval_uids_per_section_id()
        for course in self.courses:
            instructor_uids = [instructor['uid'] for instructor in course['instructors']]
            approval_uids = approval_uids_per_section_id[int(course['sectionId'])]
            all_instructors_have_approved = all(uid in approval_uids for uid in instructor_uids)
            if not all_instructors_have_approved:
                self._notify(course=course, template_type='admin_alert_instructor_change')

    def _alert_admin_of_room_changes(self):
        scheduled_rooms_per_section_id = self._get_scheduled_locations_per_section_id()
        locations_per_section_id = dict((c['sectionId'], c['meetingLocation']) for c in self.courses)
        for course in self.courses:
            section_id = course['sectionId']
            location = locations_per_section_id[section_id]
            if location != scheduled_rooms_per_section_id[int(section_id)]:
                self._notify(course=course, template_type='admin_alert_room_change')

    def _get_approval_uids_per_section_id(self):
        section_ids = [s.section_id for s in self.all_scheduled]
        all_approvals = Approval.get_approvals_per_section_ids(section_ids=section_ids, term_id=self.term_id)
        approval_uids_per_section_id = {section_id: [] for section_id in section_ids}
        for approval in all_approvals:
            approval_uids_per_section_id[approval.section_id].append(approval.approved_by_uid)
        return approval_uids_per_section_id

    def _get_scheduled_locations_per_section_id(self):
        locations_per_section_id = {}
        rooms = Room.get_rooms([s.room_id for s in self.all_scheduled])
        locations_per_room_id = dict((room.id, room.location) for room in rooms)
        for section_id, room_id in dict((s.section_id, s.room_id) for s in self.all_scheduled).items():
            locations_per_section_id[section_id] = locations_per_room_id[room_id]
        return locations_per_section_id

    def _notify(self, course, template_type):
        email_template = EmailTemplate.get_template_by_type(template_type)
        if email_template:
            message = interpolate_content(
                templated_string=email_template.message,
                course=course,
            )
            subject_line = interpolate_content(
                templated_string=email_template.subject_line,
                course=course,
            )
            QueuedEmail.create(
                message=message,
                subject_line=subject_line,
                recipients=get_admin_alert_recipients(),
                section_id=course['sectionId'],
                template_type=template_type,
                term_id=self.term_id,
            )
        else:
            raise BackgroundJobError(f"""
                No email template of type {template_type} is available.
                Diablo admin NOT notified in regard to course {course['label']}.
            """)
