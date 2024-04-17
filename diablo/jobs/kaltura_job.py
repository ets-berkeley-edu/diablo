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
from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import get_eligible_unscheduled_courses, schedule_recordings
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.kaltura_util import get_series_description
from diablo.models.email_template import EmailTemplate
from diablo.models.queued_email import notify_instructors_changes_confirmed
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import AUTHORIZED_INSTRUCTOR_ROLE_CODES, SisSection
from flask import current_app as app


class KalturaJob(BaseJob):

    def _run(self):
        _schedule_new_courses()
        # TODO update existing schedules per queued requests

    @classmethod
    def description(cls):
        return f"""
            This job:
            <ul>
                <li>Schedules recordings via Kaltura API</li>
                <li>Queues up '{EmailTemplate.get_template_type_options()['new_class_scheduled']}' emails</li>
                <li>Updates existing schedules in Kaltura</li>
            </ul>
        """

    @classmethod
    def key(cls):
        return 'kaltura'


def _get_subset_of_instructors(section_id, term_id, uids, include_deleted=False):
    course = SisSection.get_course(
        include_deleted=include_deleted,
        section_id=section_id,
        term_id=term_id,
    )
    return list(filter(lambda instructor: instructor['uid'] in uids, course['instructors']))


def _schedule_new_courses():
    term_id = app.config['CURRENT_TERM_ID']
    unscheduled_courses = get_eligible_unscheduled_courses(term_id)
    app.logger.info(f'Preparing to schedule recordings for {len(unscheduled_courses)} courses.')
    for course in unscheduled_courses:
        schedule_recordings(course, is_semester_start=False)


def _update_already_scheduled_events():
    kaltura = Kaltura()
    term_id = app.config['CURRENT_TERM_ID']
    for section_id, schedule_updates in ScheduleUpdate.get_queued_by_section_id(term_id=term_id).items():
        course = SisSection.get_course(term_id=term_id, section_id=section_id)
        for scheduled in course['scheduled']:
            kaltura_schedule = kaltura.get_event(event_id=scheduled['kalturaScheduleId'])
            scheduled_model = Scheduled.get_by_id(scheduled['id'])
            if kaltura_schedule:
                template_entry_id = kaltura_schedule['templateEntryId']
                publish_to_course_sites = scheduled.publish_type == 'kaltura_media_gallery'

                for schedule_update in schedule_updates:
                    if schedule_update.field_name == 'collaborator_uids':
                        instructors = [i for i in course['instructors'] if i['roleCode'] in AUTHORIZED_INSTRUCTOR_ROLE_CODES]
                        instructor_uids = [i['uid'] for i in instructors]
                        collaborator_uids = schedule_update.field_value_new
                        uids_entitled_to_edit = list(set(instructor_uids + collaborator_uids))
                        description = get_series_description(
                            course_label=course['label'],
                            instructors=instructors,
                            term_name=term_name_for_sis_id(term_id),
                        )
                        kaltura.update_base_entry(
                            description=description,
                            entry_id=template_entry_id,
                            name=kaltura_schedule.get('name'),
                            uids_entitled_to_edit=uids_entitled_to_edit,
                            uids_entitled_to_publish=uids_entitled_to_edit,
                        )
                        scheduled_model.update(instructor_uids=instructor_uids, collaborator_uids=collaborator_uids)

                    elif schedule_update.field_name == 'publish_type':
                        if schedule_update.field_value_new == 'kaltura_media_gallery':
                            scheduled_model.update(publish_type='kaltura_media_gallery')
                            publish_to_course_sites = True
                        elif schedule_update.field_value_new == 'kaltura_my_media':
                            scheduled_model.update(publish_type='kaltura_my_media')
                            publish_to_course_sites = False

                categories = kaltura.get_categories(template_entry_id)
                if publish_to_course_sites:
                    _add_kaltura_categories(course, categories, kaltura, template_entry_id)
                else:
                    _remove_kaltura_categories(course, categories, kaltura, template_entry_id)
            else:
                app.logger.warn(f"The previously scheduled {course['label']} schedule id {scheduled['kalturaScheduleId']} was not found in Kaltura.")
        notify_instructors_changes_confirmed(course, scheduled_model.to_api_json())


def _add_kaltura_categories(course, categories, kaltura, template_entry_id):
    for s in course.get('canvasCourseSites', []):
        canvas_course_site_id = str(s['courseSiteId'])
        if canvas_course_site_id not in [c['name'] for c in categories]:
            category = kaltura.get_canvas_category_object(canvas_course_site_id=canvas_course_site_id)
            if category:
                app.logger.info(f"{course['label']}: add Kaltura category for canvas_course_site {canvas_course_site_id}")
                kaltura.add_to_kaltura_category(
                    category_id=category['id'],
                    entry_id=template_entry_id,
                )


def _remove_kaltura_categories(course, categories, kaltura, template_entry_id):
    common_category = kaltura.get_category_object(name=app.config['KALTURA_COMMON_CATEGORY'])
    for c in categories:
        if common_category and c['id'] != common_category['id']:
            app.logger.info(f"{course['label']}: delete Kaltura category for canvas_course_site {c['name']}")
            kaltura.delete_kaltura_category(
                category_id=c['id'],
                entry_id=template_entry_id,
            )
