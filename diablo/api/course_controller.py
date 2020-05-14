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
from diablo import db
from diablo.api.errors import BadRequestError, ForbiddenRequestError, ResourceNotFoundError
from diablo.api.util import admin_required, get_search_filter_options
from diablo.externals.kaltura import Kaltura
from diablo.jobs.util import schedule_recordings
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.http import tolerant_jsonify
from diablo.merged.emailer import notify_instructors_of_approval
from diablo.models.approval import Approval, get_all_publish_types, get_all_recording_types
from diablo.models.course_preference import CoursePreference
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app, request
from flask_login import current_user, login_required
from KalturaClient.exceptions import KalturaClientException, KalturaException
from sqlalchemy import and_


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
    _notify_instructors_of_approval(
        approval=approval,
        course=course,
        previous_approvals=previous_approvals,
    )

    if app.config['FEATURE_FLAG_SCHEDULE_RECORDINGS_SYNCHRONOUSLY']:
        # This feature-flag is intended for developer workstation ONLY. Do not enable in diablo-dev|qa|prod.
        _schedule_if_has_necessary_approvals(course)

    return tolerant_jsonify(SisSection.get_course(term_id, section_id))


@app.route('/api/course/<term_id>/<section_id>')
@login_required
def get_course(term_id, section_id):
    course = SisSection.get_course(term_id, section_id)
    if not course:
        raise ResourceNotFoundError(f'No section for term_id = {term_id} and section_id = {section_id}')

    if not current_user.is_admin and current_user.uid not in [i['uid'] for i in course['instructors']]:
        raise ForbiddenRequestError(f'Sorry, you are unauthorized to view the course {course["label"]}.')
    return tolerant_jsonify(course)


@app.route('/api/courses', methods=['POST'])
@admin_required
def find_courses():
    params = request.get_json()
    term_id = params.get('termId')
    filter_ = params.get('filter', 'Not Invited')
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
    elif filter_ == 'Scheduled':
        courses = SisSection.get_courses_scheduled(term_id)
    else:
        raise BadRequestError(f'Invalid filter: {filter_}')

    return tolerant_jsonify(courses)


@app.route('/api/course/unschedule', methods=['POST'])
@admin_required
def unschedule():
    params = request.get_json()
    term_id = params.get('termId')
    section_id = params.get('sectionId')
    course = SisSection.get_course(term_id, section_id) if (term_id and section_id) else None

    if not course:
        raise BadRequestError('Required params missing or invalid')

    scheduled = course['scheduled']
    if not scheduled:
        raise BadRequestError(f'Section id {section_id}, term id {term_id} is not currently scheduled')

    db.session.execute(
        Approval.__table__.delete().where(and_(Approval.term_id == term_id, Approval.section_id == section_id)),
    )
    db.session.execute(
        Scheduled.__table__.delete().where(and_(Scheduled.term_id == term_id, Scheduled.section_id == section_id)),
    )

    kaltura_schedule_id = scheduled['kalturaScheduleId']
    try:
        Kaltura().delete_scheduled_recordings(kaltura_schedule_id)
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
    opt_out = params.get('optOut')
    preferences = CoursePreference.update_opt_out(
        term_id=term_id,
        section_id=section_id,
        opt_out=opt_out,
    )
    return tolerant_jsonify(preferences.to_api_json())


def _notify_instructors_of_approval(approval, course, previous_approvals):
    type_of_sent_email = None
    if previous_approvals:
        # Compare the current approval with preferences submitted in previous approval
        previous_approval = previous_approvals[-1]
        previous_publish_type = previous_approval.publish_type
        previous_recording_type = previous_approval.recording_type
        if approval.publish_type != previous_publish_type or approval.recording_type != previous_recording_type:
            type_of_sent_email = 'notify_instructor_of_changes'
            notify_instructors_of_approval(
                course=course,
                latest_approval=approval,
                name_of_latest_approver=current_user.name,
                previous_publish_type=previous_publish_type,
                previous_recording_type=previous_recording_type,
                template_type=type_of_sent_email,
                term_id=course['termId'],
            )
    all_approvals = previous_approvals + [approval]
    if not type_of_sent_email and len(course['instructors']) > len(all_approvals):
        approval_uids = [a.approved_by_uid for a in all_approvals]
        type_of_sent_email = 'waiting_for_approval'
        notify_instructors_of_approval(
            pending_instructors=[i for i in course['instructors'] if i['uid'] not in approval_uids],
            course=course,
            latest_approval=approval,
            name_of_latest_approver=current_user.name,
            template_type=type_of_sent_email,
            term_id=course['termId'],
        )
    return type_of_sent_email


def _schedule_if_has_necessary_approvals(course):
    def _has_necessary_approvals():
        approval_uids = [a.approved_by_uid for a in all_approvals]
        necessary_approval_uids = [i['uid'] for i in course['instructors']]
        return all(uid in approval_uids for uid in necessary_approval_uids)

    all_approvals = Approval.get_approvals(section_id=course['sectionId'], term_id=course['termId'])
    if current_user.is_admin or _has_necessary_approvals():
        scheduled = schedule_recordings(
            all_approvals=all_approvals,
            course=course,
        )
        if scheduled:
            for c in course['canvasCourseSites']:
                category_object = Kaltura().get_canvas_category_object(canvas_course_site_id=c['courseSiteId'])
                if category_object:
                    app.logger.info(f"""
                        In Kaltura, scheduled recordings of course {scheduled.section_id} will be added to
                        Canvas course site {c['courseSiteId']} (Kaltura category {category_object['id']}).
                    """)
                    Kaltura().add_scheduled_event_to_category(scheduled.kaltura_schedule_id, category_object)
