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
from diablo.externals.mailgun import Mailgun
from diablo.jobs.base_job import BaseJob
from diablo.lib.util import objects_to_dict_organized_by_section_id
from diablo.merged.emailer import interpolate_email_content
from diablo.models.approval import Approval, NAMES_PER_PUBLISH_TYPE, NAMES_PER_RECORDING_TYPE
from diablo.models.email_template import EmailTemplate
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class KalturaJob(BaseJob):

    def run(self, args=None):
        term_id = app.config['CURRENT_TERM_ID']
        approvals = Approval.get_approvals_per_term(term_id=term_id)
        if approvals:
            approvals_per_section_id = objects_to_dict_organized_by_section_id(objects=approvals)
            for course in _get_courses_ready_to_schedule(approvals=approvals, term_id=term_id):
                section_id = int(course['sectionId'])
                course_approvals = approvals_per_section_id[section_id]
                _schedule_recordings(latest_approval=course_approvals[-1], course=course)

                uids = [approval.approved_by_uid for approval in approvals]
                app.logger.info(f'Recordings scheduled recordings for course {section_id} per approvals: {", ".join(uids)}')


def _get_courses_ready_to_schedule(approvals, term_id):
    ready_to_schedule = []

    scheduled_section_ids = [s.section_id for s in Scheduled.get_all_scheduled(term_id=term_id)]
    unscheduled_approvals = [approval for approval in approvals if approval.section_id not in scheduled_section_ids]

    if unscheduled_approvals:
        courses = SisSection.get_courses(section_ids=[a.section_id for a in unscheduled_approvals], term_id=term_id)
        courses_per_section_id = dict((int(course['sectionId']), course) for course in courses)

        for section_id, uids in _get_uids_per_section_id(approvals=unscheduled_approvals).items():
            course = courses_per_section_id[section_id]
            necessary_uids = [i['uid'] for i in course['instructors']]
            if all(uid in uids for uid in necessary_uids):
                ready_to_schedule.append(courses_per_section_id[section_id])
    return ready_to_schedule


def _get_uids_per_section_id(approvals):
    uids_per_section_id = {approval.section_id: [] for approval in approvals}
    for approval in approvals:
        uids_per_section_id[approval.section_id].append(approval.approved_by_uid)
    return uids_per_section_id


def _schedule_recordings(latest_approval, course):
    section_id = int(course['sectionId'])
    Scheduled.create(section_id=section_id, term_id=course['termId'], room_id=latest_approval.room_id)
    _notify_instructors(course=course, latest_approval=latest_approval)


def _notify_instructors(course, latest_approval):
    email_template = EmailTemplate.get_template_by_type('recordings_scheduled')
    publish_type_name = NAMES_PER_PUBLISH_TYPE[latest_approval.publish_type]
    recording_type_name = NAMES_PER_RECORDING_TYPE[latest_approval.recording_type]
    Mailgun().send(
        message=interpolate_email_content(
            course=course,
            publish_type_name=publish_type_name,
            recording_type_name=recording_type_name,
            templated_string=email_template.message,
        ),
        recipients=course['instructors'],
        section_id=course['sectionId'],
        subject_line=interpolate_email_content(
            course=course,
            publish_type_name=publish_type_name,
            recording_type_name=recording_type_name,
            templated_string=email_template.subject_line,
        ),
        template_type=email_template.template_type,
        term_id=course['termId'],
    )
