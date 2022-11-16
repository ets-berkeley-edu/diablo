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
from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import get_courses_ready_to_schedule, schedule_recordings
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.kaltura_util import get_series_description
from diablo.lib.util import objects_to_dict_organized_by_section_id
from diablo.models.approval import Approval
from diablo.models.email_template import EmailTemplate
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
    term_id = app.config['CURRENT_TERM_ID']
    for course in SisSection.get_courses_scheduled(term_id=term_id):
        course_name = course['label']
        scheduled = course['scheduled']
        kaltura_schedule = kaltura.get_event(event_id=scheduled['kalturaScheduleId'])
        if kaltura_schedule:
            template_entry_id = kaltura_schedule['templateEntryId']
            if course['canvasCourseSites'] and scheduled['publishType'] == 'kaltura_media_gallery':
                # From Kaltura, get Canvas course sites (categories) currently mapped to the course.
                categories = kaltura.get_categories(template_entry_id)

                for s in course['canvasCourseSites']:
                    canvas_course_site_id = str(s['courseSiteId'])
                    if canvas_course_site_id not in [c['name'] for c in categories]:
                        _update_kaltura_category(
                            canvas_course_site_id=canvas_course_site_id,
                            course_name=course_name,
                            kaltura=kaltura,
                            template_entry_id=template_entry_id,
                        )
            # Update Kaltura edit permissions per UID.
            uids_entitled_to_edit = set(scheduled['instructorUids'])
            if course['canAprxInstructorsEditRecordings']:
                instructors = course['instructors']
                aprx_uids = list(filter(lambda i: i['roleCode'] == 'APRX' and not i['deletedAt'], instructors))
                uids_entitled_to_edit.update(aprx_uids)
            uids_entitled_to_edit = list(uids_entitled_to_edit)
            instructors_entitled_to_edit = SisSection.get_instructors(include_deleted=True, uids=uids_entitled_to_edit)
            description = get_series_description(
                course_label=course_name,
                instructors=instructors_entitled_to_edit,
                term_name=term_name_for_sis_id(term_id),
            )
            kaltura.update_base_entry(
                description=description,
                entry_id=template_entry_id,
                name=kaltura_schedule.get('name'),
                uids_entitled_to_edit=uids_entitled_to_edit,
                uids_entitled_to_publish=uids_entitled_to_edit,
            )
        else:
            app.logger.warn(f'The previously scheduled {course_name} has no schedule_event in Kaltura.')


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
        ready_to_schedule = get_courses_ready_to_schedule(approvals=approvals, term_id=term_id)
        app.logger.info(f'Prepare to schedule recordings for {len(ready_to_schedule)} courses.')
        for course in ready_to_schedule:
            section_id = int(course['sectionId'])
            schedule_recordings(
                all_approvals=approvals_per_section_id[section_id],
                course=course,
            )
