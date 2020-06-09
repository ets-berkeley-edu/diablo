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

from diablo.api.errors import BadRequestError, ForbiddenRequestError, ResourceNotFoundError
from diablo.api.util import admin_required, csv_download_response, get_search_filter_options
from diablo.externals.kaltura import Kaltura
from diablo.jobs.util import schedule_recordings
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.http import tolerant_jsonify
from diablo.lib.interpolator import get_sign_up_url
from diablo.models.approval import Approval, get_all_publish_types, get_all_recording_types
from diablo.models.course_preference import CoursePreference
from diablo.models.queued_email import notify_instructor_waiting_for_approval, notify_instructors_of_changes
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app, request
from flask_login import current_user, login_required
from KalturaClient.exceptions import KalturaClientException, KalturaException


@app.route('/api/course/approve', methods=['POST'])
@login_required
def approve():
    term_id = app.config['CURRENT_TERM_ID']
    term_name = term_name_for_sis_id(term_id)

    params = request.get_json()
    publish_type = params.get('publishType')
    recording_type = params.get('recordingType')
    section_id = params.get('sectionId')

    course = SisSection.get_course(term_id, section_id) if section_id else None

    if not course or publish_type not in get_all_publish_types() or recording_type not in get_all_recording_types():
        raise BadRequestError('One or more required params are missing or invalid')

    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError('Sorry, request unauthorized')

    if Approval.get_approval(approved_by_uid=current_user.uid, section_id=section_id, term_id=term_id):
        raise ForbiddenRequestError(f'You have already approved recording of {course["courseName"]}, {term_name}')

    location = course['meetingLocation']
    room = Room.find_room(location=location)
    if not room:
        raise BadRequestError(f'{location} is not eligible for Course Capture.')

    previous_approvals = Approval.get_approvals_per_section_ids(section_ids=[section_id], term_id=term_id)
    approval = Approval.create(
        approved_by_uid=current_user.uid,
        approver_type_='admin' if current_user.is_admin else 'instructor',
        publish_type_=publish_type,
        recording_type_=recording_type,
        room_id=room.id,
        section_id=section_id,
        term_id=term_id,
    )

    if previous_approvals:
        # Compare the current approval with preferences submitted in previous approval
        previous_approval = previous_approvals[-1]
        if (approval.publish_type, approval.recording_type) != (previous_approval.publish_type, previous_approval.recording_type):
            notify_instructors_of_changes(course, approval, previous_approvals)

    all_approvals = previous_approvals + [approval]
    if len(course['instructors']) > len(all_approvals):
        approval_uids = [a.approved_by_uid for a in all_approvals]
        pending_instructors = [i for i in course['instructors'] if i['uid'] not in approval_uids]
        last_approver = next((i for i in course['instructors'] if i['uid'] == approval.approved_by_uid), None)
        if last_approver:
            notify_instructor_waiting_for_approval(course, last_approver, pending_instructors)

    _update_scheduling(course)

    return tolerant_jsonify(SisSection.get_course(term_id, section_id))


@app.route('/api/course/<term_id>/<section_id>')
@login_required
def get_course(term_id, section_id):
    course = SisSection.get_course(term_id, section_id)
    if not course:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')
    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')

    if current_user.is_admin and course['scheduled']:
        # When debugging, the raw Kaltura-provided JSON is useful.
        kaltura_schedule_id = course['scheduled'].get('kalturaScheduleId')
        course['scheduled']['kalturaSchedule'] = Kaltura().get_schedule_event(kaltura_schedule_id)

    return tolerant_jsonify(course)


@app.route('/api/courses', methods=['POST'])
@admin_required
def find_courses():
    params = request.get_json()
    term_id = params.get('termId')
    filter_ = params.get('filter', 'Not Invited')
    return tolerant_jsonify(_get_courses_per_filter(filter_=filter_, term_id=term_id))


@app.route('/api/courses/csv', methods=['POST'])
@admin_required
def download_courses_csv():
    def _get_email_with_label(instructor):
        email = instructor.get('email')
        name = instructor.get('name') or instructor.get('uid')
        return f'{name} <{email}>' if email else name

    def _course_csv_row(c):
        section_id = c.get('sectionId')
        scheduled = c.get('scheduled') or {}
        return {
            'Course Name': c.get('courseName'),
            'Section Id': section_id,
            'Room': c.get('meetingLocation'),
            'Days': ', '.join(c.get('meetingDays') or []),
            'Start Time': c.get('meetingStartTime'),
            'End Time': c.get('meetingEndTime'),
            'Publish Type': scheduled.get('publishTypeName'),
            'Recording Type': scheduled.get('recordingTypeName'),
            'Sign-up URL': get_sign_up_url(section_id=section_id, term_id=c.get('termId')),
            'Canvas URLs': [f"{app.config['CANVAS_BASE_URL']}/courses/{s['courseSiteId']}" for s in c.get('canvasCourseSites') or []],
            'Instructors': ', '.join([_get_email_with_label(instructor) for instructor in c.get('instructors') or []]),
            'Instructor UIDs': ', '.join([instructor.get('uid') for instructor in c.get('instructors') or []]),
        }

    params = request.get_json()
    term_id = params.get('termId')
    filter_ = params.get('filter', 'Not Invited')
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return csv_download_response(
        rows=[_course_csv_row(c) for c in _get_courses_per_filter(filter_=filter_, term_id=term_id)],
        filename=f"courses-{filter_.lower().replace(' ', '_')}-{term_id}_{now}.csv",
        fieldnames=list(_course_csv_row({}).keys()),
    )


@app.route('/api/course/unschedule', methods=['POST'])
@admin_required
def unschedule():
    params = request.get_json()
    term_id = params.get('termId')
    section_id = params.get('sectionId')
    course = SisSection.get_course(term_id, section_id) if (term_id and section_id) else None

    if not course:
        raise BadRequestError('Required params missing or invalid')

    if not (course['scheduled'] or course['hasNecessaryApprovals']):
        raise BadRequestError(f'Section id {section_id}, term id {term_id} is not currently scheduled or queued for scheduling')

    kaltura_schedule_id = (course.get('scheduled') or {}).get('kalturaScheduleId')
    Approval.delete(term_id=term_id, section_id=section_id)
    Scheduled.delete(term_id=term_id, section_id=section_id)

    if kaltura_schedule_id:
        try:
            Kaltura().delete_event(kaltura_schedule_id)
        except (KalturaClientException, KalturaException) as e:
            app.logger.error(f'Failed to delete Kaltura schedule: {kaltura_schedule_id}')
            app.logger.exception(e)

    CoursePreference.update_opt_out(
        term_id=term_id,
        section_id=section_id,
        opt_out=True,
    )
    return tolerant_jsonify(SisSection.get_course(term_id, section_id))


@app.route('/api/courses/changes/<term_id>')
@admin_required
def course_changes(term_id):
    return tolerant_jsonify(SisSection.get_course_changes(term_id))


@app.route('/api/course/opt_out/update', methods=['POST'])
@admin_required
def update_opt_out():
    params = request.get_json()
    term_id = params.get('termId')
    section_id = params.get('sectionId')

    course = SisSection.get_course(term_id, section_id) if (term_id and section_id) else None
    opt_out = params.get('optOut')
    if not course or opt_out is None:
        raise BadRequestError('Required params missing or invalid')
    if course['scheduled']:
        raise BadRequestError('Cannot update opt-out on scheduled course')

    preferences = CoursePreference.update_opt_out(
        term_id=term_id,
        section_id=section_id,
        opt_out=opt_out,
    )
    return tolerant_jsonify(preferences.to_api_json())


def _get_courses_per_filter(filter_, term_id):
    if filter_ not in get_search_filter_options() or not term_id:
        raise BadRequestError('One or more required params are missing or invalid')

    if filter_ == 'All':
        courses = SisSection.get_courses(term_id)
    elif filter_ == 'Do Not Email':
        courses = SisSection.get_courses_opted_out(term_id)
    elif filter_ == 'Invited':
        courses = SisSection.get_courses_invited(term_id)
    elif filter_ == 'Not Invited':
        courses = SisSection.get_eligible_courses_not_invited(term_id)
    elif filter_ == 'Partially Approved':
        courses = SisSection.get_courses_partially_approved(term_id)
    elif filter_ == 'Queued for Scheduling':
        courses = SisSection.get_courses_queued_for_scheduling(term_id)
    elif filter_ == 'Scheduled':
        courses = SisSection.get_courses_scheduled(term_id)
    else:
        raise BadRequestError(f'Invalid filter: {filter_}')
    return courses


def _update_scheduling(course):
    def _has_necessary_approvals():
        approval_uids = [a.approved_by_uid for a in all_approvals]
        necessary_approval_uids = [i['uid'] for i in course['instructors']]
        return all(uid in approval_uids for uid in necessary_approval_uids)

    all_approvals = Approval.get_approvals(section_id=course['sectionId'], term_id=course['termId'])
    if not course['scheduled'] and (current_user.is_admin or _has_necessary_approvals()):
        # Queuing a course for scheduling wipes any opt-out preference.
        if course['hasOptedOut']:
            CoursePreference.update_opt_out(
                term_id=course['termId'],
                section_id=course['sectionId'],
                opt_out=False,
            )
        # This feature flag is intended for developer workstation ONLY. Do not enable in diablo-dev|qa|prod.
        if app.config['FEATURE_FLAG_SCHEDULE_RECORDINGS_SYNCHRONOUSLY']:
            schedule_recordings(
                all_approvals=all_approvals,
                course=course,
            )
