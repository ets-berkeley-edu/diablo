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
from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import schedule_recordings
from diablo.lib.util import objects_to_dict_organized_by_section_id
from diablo.models.admin_user import AdminUser
from diablo.models.approval import Approval
from diablo.models.email_template import EmailTemplate
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class KalturaJob(BaseJob):

    def _run(self):
        _update_already_scheduled_events()
        _schedule_the_ready_to_schedule()

    @classmethod
    def description(cls):
        return f"""
            This job:
            <ul>
                <li>Schedules recordings via Kaltura API</li>
                <li>Queues up '{EmailTemplate.get_template_type_options()['recordings_scheduled']}' emails</li>
                <li>Updates existing schedules in Kaltura</li>
            </ul>
        """

    @classmethod
    def key(cls):
        return 'kaltura'


def _update_already_scheduled_events():
    kaltura = Kaltura()
    for course in SisSection.get_courses_scheduled(term_id=app.config['CURRENT_TERM_ID']):
        course_name = course['label']
        scheduled = course['scheduled']
        kaltura_schedule = kaltura.get_event(event_id=scheduled['kalturaScheduleId'])
        if kaltura_schedule and course['canvasCourseSites'] and scheduled['publishType'] == 'kaltura_media_gallery':
            # From Kaltura, get Canvas course sites (categories) currently mapped to the course.
            template_entry_id = kaltura_schedule['templateEntryId']
            categories = kaltura.get_categories(template_entry_id)

            for s in course['canvasCourseSites']:
                canvas_course_site_id = str(s['courseSiteId'])
                if canvas_course_site_id not in [c['courseSiteId'] for c in categories]:
                    _update_kaltura_category(canvas_course_site_id, course_name, kaltura, template_entry_id)
        else:
            app.logger.warn(f'The previously scheduled {course_name} has no schedule_event in Kaltura.')


def _get_entitled_users(kaltura_base_entry):
    entitled_users = kaltura_base_entry['entitledUsersEdit']
    return entitled_users.split(',') if entitled_users else []


def _update_kaltura_category(canvas_course_site_id, course_name, kaltura, template_entry_id):
    category = kaltura.get_canvas_category_object(canvas_course_site_id=canvas_course_site_id)
    if category:
        app.logger.info(f'{course_name}: add Kaltura category for canvas_course_site {canvas_course_site_id}')
        kaltura.add_to_kaltura_category(
            category_id=category['id'],
            entry_id=template_entry_id,
        )


def _schedule_the_ready_to_schedule():
    term_id = app.config['CURRENT_TERM_ID']
    approvals = Approval.get_approvals_per_term(term_id=term_id)
    if approvals:
        approvals_per_section_id = objects_to_dict_organized_by_section_id(objects=approvals)
        ready_to_schedule = _get_courses_ready_to_schedule(approvals=approvals, term_id=term_id)
        app.logger.info(f'Prepare to schedule recordings for {len(ready_to_schedule)} courses.')
        for course in ready_to_schedule:
            section_id = int(course['sectionId'])
            schedule_recordings(
                all_approvals=approvals_per_section_id[section_id],
                course=course,
            )


def _get_courses_ready_to_schedule(approvals, term_id):
    ready_to_schedule = []

    scheduled_section_ids = [s.section_id for s in Scheduled.get_all_scheduled(term_id=term_id)]
    unscheduled_approvals = [approval for approval in approvals if approval.section_id not in scheduled_section_ids]

    if unscheduled_approvals:
        courses = SisSection.get_courses(section_ids=[a.section_id for a in unscheduled_approvals], term_id=term_id)
        courses_per_section_id = dict((int(course['sectionId']), course) for course in courses)
        admin_user_uids = set([user.uid for user in AdminUser.all_admin_users(include_deleted=True)])

        for section_id, uids in _get_uids_per_section_id(approvals=unscheduled_approvals).items():
            course = courses_per_section_id.get(section_id)
            if not course:
                continue
            if len(course.get('meetings', {}).get('eligible', [])) != 1:
                app.logger.warn(f'Unique meeting pattern not found for section id {section_id}; will not schedule.')
                continue
            if admin_user_uids.intersection(set(uids)):
                ready_to_schedule.append(course)
            else:
                necessary_uids = [i['uid'] for i in course['instructors']]
                if all(uid in uids for uid in necessary_uids):
                    ready_to_schedule.append(course)
    return ready_to_schedule


def _get_uids_per_section_id(approvals):
    uids_per_section_id = {approval.section_id: [] for approval in approvals}
    for approval in approvals:
        uids_per_section_id[approval.section_id].append(approval.approved_by_uid)
    return uids_per_section_id
