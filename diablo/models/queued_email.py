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
from datetime import datetime

from diablo import db, std_commit
from diablo.externals.loch import get_loch_basic_attributes
from diablo.lib.interpolator import interpolate_content
from diablo.lib.util import to_isoformat
from diablo.merged.emailer import get_admin_alert_recipient, send_system_error_email
from diablo.models.course_preference import NAMES_PER_PUBLISH_TYPE, NAMES_PER_RECORDING_TYPE
from diablo.models.email_template import email_template_type, EmailTemplate
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES, SisSection
from flask import current_app as app
from sqlalchemy.dialects.postgresql import JSONB


class QueuedEmail(db.Model):
    __tablename__ = 'queued_emails'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    subject_line = db.Column(db.String(255))
    message = db.Column(db.Text)
    recipient = db.Column(JSONB)
    section_id = db.Column(db.Integer, nullable=False)
    template_type = db.Column(email_template_type, nullable=False)
    term_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (db.UniqueConstraint(
        'section_id',
        'template_type',
        'term_id',
        name='queued_emails_section_id_template_type_unique_constraint',
    ),)

    def __init__(self, section_id, template_type, term_id, recipient, message=None, subject_line=None):
        self.template_type = template_type
        self.section_id = section_id
        self.term_id = term_id
        self.recipient = recipient
        self.message = message
        self.subject_line = subject_line

    def __repr__(self):
        return f"""<QueuedEmail
                    id={self.id}
                    section_id={self.section_id},
                    template_type={self.template_type}
                    term_id={self.term_id},
                    recipient={self.recipient},
                    message={self.message},
                    subject_line={self.subject_line},
                    created_at={self.created_at}
                """

    @classmethod
    def create(cls, section_id, template_type, term_id, recipient, message=None, subject_line=None):
        course = SisSection.get_course(term_id, section_id, include_deleted=True)
        if not course:
            app.logger.error(f'Attempt to queue email for unknown course (term_id={term_id}, section_id={section_id})')
            return
        if not course['instructors']:
            app.logger.error(f'Attempt to queue email for course without instructors (term_id={term_id}, section_id={section_id})')
            return
        queued_email = cls(
            section_id=section_id,
            template_type=template_type,
            term_id=term_id,
            recipient=recipient,
            message=message,
            subject_line=subject_line,
        )
        course = SisSection.get_course(term_id, queued_email.section_id, include_deleted=True)
        if not queued_email.is_interpolated() and not queued_email.interpolate(course):
            app.logger.error(f'Failed to interpolate all required values for queued email ({queued_email})')
            return
        db.session.add(queued_email)
        std_commit()
        return queued_email

    @classmethod
    def delete(cls, queued_email):
        db.session.delete(queued_email)
        std_commit()

    @classmethod
    def get_all(cls, term_id):
        return cls.query.filter_by(term_id=term_id).order_by(cls.created_at).all()

    @classmethod
    def get_all_section_ids(cls, template_type, term_id):
        return [row.section_id for row in cls.query.filter_by(template_type=template_type, term_id=term_id).all()]

    @classmethod
    def notify_admin_operator_requested(cls, course):
        cls._queue_admin_email('admin_operator_requested', course)

    @classmethod
    def notify_instructors_changes_confirmed(cls, course, collaborator_uids, publish_type, recording_type):
        publish_type_name = NAMES_PER_PUBLISH_TYPE[publish_type]
        recording_type_name = NAMES_PER_RECORDING_TYPE[recording_type]
        if collaborator_uids:
            collaborator_attributes = get_loch_basic_attributes(collaborator_uids)
            collaborator_names = [f"{r['first_name']} {r['last_name']}" for r in collaborator_attributes]
        else:
            collaborator_names = []

        for instructor in filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES, course['instructors']):
            cls._queue_instructor_email(
                'changes_confirmed',
                instructor,
                course,
                publish_type_name=publish_type_name,
                recording_type_name=recording_type_name,
                collaborator_names=collaborator_names,
            )

    @classmethod
    def notify_instructors_no_longer_scheduled(cls, course):
        for instructor in filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES, course['instructors']):
            cls._queue_instructor_email('no_longer_scheduled', instructor, course)

    @classmethod
    def notify_instructors_no_longer_eligible(cls, course):
        for instructor in filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES, course['instructors']):
            cls._queue_instructor_email('room_change_no_longer_eligible', instructor, course)

    @classmethod
    def notify_instructors_schedule_change(cls, course):
        for instructor in filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES, course['instructors']):
            cls._queue_instructor_email('schedule_change', instructor, course)

    @classmethod
    def notify_instructor_added(cls, instructor, course):
        cls._queue_instructor_email('instructors_added', instructor, course)

    @classmethod
    def notify_instructor_removed(cls, instructor, course):
        cls._queue_instructor_email('instructors_removed', instructor, course)

    @classmethod
    def _queue_admin_email(cls, template_type, course, **kwargs):
        template = _get_email_template(course=course, template_type=template_type)
        if template:
            recipient = get_admin_alert_recipient()
            message = interpolate_content(
                templated_string=template.message,
                course=course,
                recipient_name=recipient['name'],
            )
            subject_line = interpolate_content(
                templated_string=template.subject_line,
                course=course,
                recipient_name=recipient['name'],
            )
            cls.create(
                message=message,
                subject_line=subject_line,
                recipient=recipient,
                section_id=course['sectionId'],
                template_type=template_type,
                term_id=course['termId'],
            )

    @classmethod
    def _queue_instructor_email(cls, template_type, instructor, course, **kwargs):
        template = _get_email_template(course=course, template_type=template_type)
        if template:
            message = interpolate_content(
                templated_string=template.message,
                course=course,
                recipient_name=instructor['name'],
                **kwargs,
            )
            subject_line = interpolate_content(
                templated_string=template.subject_line,
                course=course,
                recipient_name=instructor['name'],
            )
            cls.create(
                message=message,
                subject_line=subject_line,
                recipient=instructor,
                section_id=course['sectionId'],
                template_type=template_type,
                term_id=course['termId'],
            )

    def is_interpolated(self):
        return not (self.subject_line is None or self.message is None or self.recipient is None)

    def interpolate(self, course):
        template = _get_email_template(course=course, template_type=self.template_type)
        if template:
            self.subject_line = interpolate_content(
                course=course,
                templated_string=template.subject_line,
                recipient_name=self.recipient['name'],
            )
            self.message = interpolate_content(
                course=course,
                templated_string=template.message,
                recipient_name=self.recipient['name'],
            )
            db.session.add(self)
            std_commit()
            # Return True only if all required data has been set.
            return self.is_interpolated

    def to_api_json(self):
        return {
            'id': self.id,
            'sectionId': self.section_id,
            'templateType': self.template_type,
            'templateTypeName': EmailTemplate.get_template_type_options()[self.template_type],
            'termId': self.term_id,
            'createdAt': to_isoformat(self.created_at),
        }


def _get_email_template(course, template_type):
    template = EmailTemplate.get_template_by_type(template_type)
    if not template:
        subject = f"No {template_type} email template found; failed to queue email for section_id {course['sectionId']}"
        send_system_error_email(
            message=f'{subject}\n\n<pre>{course}</pre>',
            subject=subject,
        )
    return template


def announce_semester_start(instructor, courses):
    template = _get_email_template(course=courses[0], template_type='semester_start')
    if not template:
        return
    message = interpolate_content(
        templated_string=template.message,
        recipient_name=instructor['name'],
        course=None,
        course_list=courses,
    )
    QueuedEmail.create(
        message=message,
        recipient=instructor,
        section_id=courses[0]['sectionId'],
        subject_line=template.subject_line,
        template_type='semester_start',
        term_id=courses[0]['termId'],
    )


def notify_instructors_recordings_scheduled(course, scheduled, template_type):
    email_template = EmailTemplate.get_template_by_type(template_type)
    if email_template:
        publish_type_name = NAMES_PER_PUBLISH_TYPE[scheduled.publish_type]
        recording_type_name = NAMES_PER_RECORDING_TYPE[scheduled.recording_type]
        instructors = list(filter(lambda i: i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES, course['instructors']))
        for instructor in instructors:
            message = interpolate_content(
                templated_string=email_template.message,
                course=course,
                recipient_name=instructor['name'],
                publish_type_name=publish_type_name,
                recording_type_name=recording_type_name,
            )
            subject_line = interpolate_content(
                templated_string=email_template.subject_line,
                course=course,
                recipient_name=instructor['name'],
            )
            QueuedEmail.create(
                message=message,
                subject_line=subject_line,
                recipient=instructor,
                section_id=course['sectionId'],
                template_type=email_template.template_type,
                term_id=course['termId'],
            )
    else:
        send_system_error_email(f"""
            No email template of type {template_type} is available.
            {course['label']} instructors were NOT notified of scheduled: {scheduled}.
        """)


def remind_instructors_scheduled(instructor, courses):
    template = _get_email_template(course=courses[0], template_type='remind_scheduled')
    if not template:
        return
    message = interpolate_content(
        templated_string=template.message,
        recipient_name=instructor['name'],
        course=None,
        course_list=courses,
    )
    QueuedEmail.create(
        message=message,
        recipient=instructor,
        section_id=courses[0]['sectionId'],
        subject_line=template.subject_line,
        template_type='remind_scheduled',
        term_id=courses[0]['termId'],
    )
