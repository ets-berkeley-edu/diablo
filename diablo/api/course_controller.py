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
import re

from diablo.api.errors import BadRequestError, ForbiddenRequestError, InternalServerError, ResourceNotFoundError
from diablo.api.util import admin_required, csv_download_response, get_search_filter_options
from diablo.externals.kaltura import Kaltura
from diablo.lib.http import tolerant_jsonify
from diablo.lib.interpolator import get_sign_up_url
from diablo.models.course_preference import CoursePreference, get_all_publish_types, get_all_recording_types
from diablo.models.opt_out import OptOut
from diablo.models.schedule_update import ScheduleUpdate
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app, request
from flask_login import current_user, login_required


@app.route('/api/course/<term_id>/<section_id>')
@login_required
def get_course(term_id, section_id):
    course = SisSection.get_course(
        term_id,
        section_id,
        include_administrative_proxies=True,
        include_deleted=True,
        include_update_history=True,
    )
    if not course:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')
    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')

    if current_user.is_admin and course['scheduled']:
        # When debugging, the raw Kaltura-provided JSON is useful.
        for scheduled in course['scheduled']:
            event_id = scheduled.get('kalturaScheduleId')
            scheduled['kalturaSchedule'] = Kaltura().get_event(event_id)
    return tolerant_jsonify(course)


@app.route('/api/courses', methods=['POST'])
@admin_required
def find_courses():
    params = request.get_json()
    term_id = params.get('termId')
    filter_ = params.get('filter', 'Scheduled')
    return tolerant_jsonify(_get_courses_per_filter(filter_=filter_, term_id=term_id))


@app.route('/api/courses/csv', methods=['POST'])
@admin_required
def download_courses_csv():
    def _get_email_with_label(instructor):
        email = instructor.get('email')
        name = instructor.get('name') or instructor.get('uid')
        return f'{name} <{email}>' if email else name

    def _course_csv_row(c, scheduled):
        course_name = c.get('courseName')
        instruction_format = c.get('instructionFormat')
        eligible_meetings = c.get('meetings', {}).get('eligible', [])
        section_id = c.get('sectionId')
        return {
            'Course Name': f"{course_name}, {instruction_format} {c.get('sectionNum')}" if instruction_format else course_name,
            'Section Id': section_id,
            'Room': ' / '.join(m.get('location', '') for m in eligible_meetings),
            'Days': ' / '.join(', '.join(m.get('daysFormatted') or []) for m in eligible_meetings),
            'Start Time': ' / '.join((m.get('startTimeFormatted') or '') for m in eligible_meetings),
            'End Time': ' / '.join((m.get('endTimeFormatted') or '') for m in eligible_meetings),
            'Meeting Type': c.get('meetingType'),
            'Publish Type': scheduled.get('publishTypeName'),
            'Recording Type': scheduled.get('recordingTypeName'),
            'Sign-up URL': get_sign_up_url(section_id=section_id, term_id=c.get('termId')),
            'Canvas URL': f"{app.config['CANVAS_BASE_URL']}/courses/{c['canvasSiteId']}" if c.get('canvasSiteId') else '',
            'Instructors': ', '.join([_get_email_with_label(instructor) for instructor in c.get('instructors') or []]),
            'Instructor UIDs': ', '.join([instructor.get('uid') for instructor in c.get('instructors') or []]),
            'Collaborator UIDs': ', '.join([u for u in c.get('collaboratorUids') or []]),
        }

    params = request.get_json()
    term_id = params.get('termId')
    filter_ = params.get('filter', 'Scheduled')
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    rows = []
    for c in _get_courses_per_filter(filter_=filter_, term_id=term_id):
        for scheduled in (c['scheduled'] or [{}]):
            rows.append(_course_csv_row(c, scheduled))
    return csv_download_response(
        rows=rows,
        filename=f"courses-{filter_.lower().replace(' ', '_')}-{term_id}_{now}.csv",
        fieldnames=list(_course_csv_row({}, {}).keys()),
    )


@app.route('/api/course/collaborator_uids/update', methods=['POST'])
@login_required
def update_collaborator_uids():
    params = request.get_json()
    section_id = params.get('sectionId')
    term_id = params.get('termId')
    collaborator_uids = params.get('collaboratorUids') or []

    course = SisSection.get_course(term_id, section_id) if (term_id and section_id) else None
    if not course or type(collaborator_uids) != list:
        raise BadRequestError('Required params missing or invalid')
    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')

    preferences = CoursePreference.update_collaborator_uids(
        term_id=term_id,
        section_id=section_id,
        collaborator_uids=collaborator_uids,
    )
    if preferences:
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='collaborator_uids',
            field_value_old=course.get('collaboratorUids'),
            field_value_new=collaborator_uids,
            requested_by_uid=current_user.uid,
            requested_by_name=current_user.name,
        )

    return tolerant_jsonify(preferences.to_api_json())


@app.route('/api/course/opt_out/update', methods=['POST'])
@login_required
def update_opt_out():
    params = request.get_json()
    instructor_uid = params.get('instructorUid')
    term_id = params.get('termId')
    section_id = params.get('sectionId')
    opt_out = params.get('optOut')
    if opt_out is None or not instructor_uid or not term_id or not section_id:
        raise BadRequestError('Required params missing or invalid')

    if str(instructor_uid) != str(current_user.uid) and not current_user.is_admin:
        raise ForbiddenRequestError(f'Unable to update opt-out preferences for UID {instructor_uid}.')

    if term_id == 'all':
        # Global opt-out for user.
        term_id = None
        section_id = None

    elif re.match(r'2\d{3}', str(term_id)) and section_id == 'all':
        # Per-term opt-cut for user.
        section_id = None

    else:
        # Per-course opt-out.
        course = SisSection.get_course(term_id, section_id)
        if not course:
            raise BadRequestError('Required params missing or invalid')
        if not current_user.is_admin and str(instructor_uid) not in [str(i['uid']) for i in course['instructors']]:
            raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')

    def _schedule_opt_out_update(scheduled_section_id, scheduled_term_id):
        if opt_out:
            ScheduleUpdate.queue(
                term_id=scheduled_term_id,
                section_id=scheduled_section_id,
                field_name='opted_out',
                field_value_old=None,
                field_value_new=instructor_uid,
                requested_by_uid=current_user.uid,
                requested_by_name=current_user.name,
            )
        else:
            ScheduleUpdate.queue(
                term_id=scheduled_term_id,
                section_id=scheduled_section_id,
                field_name='opted_out',
                field_value_old=instructor_uid,
                field_value_new=None,
                requested_by_uid=current_user.uid,
                requested_by_name=current_user.name,
            )

    if OptOut.update_opt_out(
        instructor_uid=instructor_uid,
        term_id=term_id,
        section_id=section_id,
        opt_out=opt_out,
    ):
        if section_id:
            _schedule_opt_out_update(section_id, term_id)
        else:
            for scheduled_section_id in Scheduled.get_scheduled_per_instructor_uid(instructor_uid, app.config['CURRENT_TERM_ID']):
                _schedule_opt_out_update(scheduled_section_id, app.config['CURRENT_TERM_ID'])
        return tolerant_jsonify({'optedOut': opt_out})
    else:
        raise InternalServerError('Failed to update opt-out.')


@app.route('/api/course/publish_type/update', methods=['POST'])
@login_required
def update_publish_type():
    params = request.get_json()
    section_id = params.get('sectionId')
    term_id = params.get('termId')
    publish_type = params.get('publishType') or None
    canvas_site_id = params.get('canvasSiteId') or None

    course = SisSection.get_course(term_id, section_id) if (term_id and section_id) else None
    if not course or (publish_type not in get_all_publish_types()):
        raise BadRequestError('Required params missing or invalid')
    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')
    if publish_type and publish_type.startswith('kaltura_media_gallery') and not canvas_site_id:
        raise BadRequestError('Publication to course site requires Canvas site id')

    preferences = CoursePreference.update_publish_type(
        term_id=term_id,
        section_id=section_id,
        publish_type=publish_type,
        canvas_site_id=canvas_site_id,
    )
    if preferences:
        if course.get('publishType') != publish_type:
            ScheduleUpdate.queue(
                term_id=course['termId'],
                section_id=course['sectionId'],
                field_name='publish_type',
                field_value_old=course.get('publishType'),
                field_value_new=publish_type,
                requested_by_uid=current_user.uid,
                requested_by_name=current_user.name,
            )
        if course.get('canvasSiteId') != canvas_site_id:
            ScheduleUpdate.queue(
                term_id=course['termId'],
                section_id=course['sectionId'],
                field_name='canvas_site_id',
                field_value_old=course.get('canvasSiteId'),
                field_value_new=canvas_site_id,
                requested_by_uid=current_user.uid,
                requested_by_name=current_user.name,
            )

    return tolerant_jsonify(preferences.to_api_json())


@app.route('/api/course/recording_type/update', methods=['POST'])
@login_required
def update_recording_type():
    params = request.get_json()
    section_id = params.get('sectionId')
    term_id = params.get('termId')
    recording_type = params.get('recordingType') or None

    course = SisSection.get_course(term_id, section_id) if (term_id and section_id) else None
    if not course or (recording_type not in get_all_recording_types()):
        raise BadRequestError('Required params missing or invalid')
    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')

    preferences = CoursePreference.update_recording_type(
        term_id=term_id,
        section_id=section_id,
        recording_type=recording_type,
    )
    if preferences:
        ScheduleUpdate.queue(
            term_id=course['termId'],
            section_id=course['sectionId'],
            field_name='recording_type',
            field_value_old=course.get('recordingType'),
            field_value_new=recording_type,
            requested_by_uid=current_user.uid,
            requested_by_name=current_user.name,
        )

    return tolerant_jsonify(preferences.to_api_json())


@app.route('/api/courses/report/<term_id>')
@admin_required
def courses_report(term_id):
    return tolerant_jsonify({
        'totalScheduledCount': len(Scheduled.get_all_scheduled(term_id=term_id)),
    })


def _get_courses_per_filter(filter_, term_id):
    if filter_ not in get_search_filter_options() or not term_id:
        raise BadRequestError('One or more required params are missing or invalid')

    if filter_ == 'All':
        courses = SisSection.get_courses(term_id)
    elif filter_ == 'Opted Out':
        courses = SisSection.get_courses_opted_out(term_id)
    elif filter_ == 'Scheduled':
        courses = SisSection.get_courses_scheduled(term_id)
    elif filter_ == 'No Instructors':
        courses = SisSection.get_courses_without_instructors(term_id)
    else:
        raise BadRequestError(f'Invalid filter: {filter_}')
    return courses
