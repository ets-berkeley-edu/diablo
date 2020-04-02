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
from diablo.externals.mailgun import send_email
from diablo.jobs.base_job import BaseJob
from diablo.merged.emailer import interpolate_email_content
from diablo.merged.sis import get_courses
from diablo.models.email_template import EmailTemplate
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from flask import current_app as app


class EmailAlertsForAdmins(BaseJob):

    def run(self, args=None):
        term_id = app.config['CURRENT_TERM_ID']
        all_scheduled = Scheduled.get_all_scheduled(term_id=term_id)
        if all_scheduled:
            scheduled_rooms_per_section_id = _scheduled_locations_per_section_id(all_scheduled)
            courses = get_courses(term_id=term_id, section_ids=[s.section_id for s in all_scheduled])
            locations_per_section_id = dict((c['sectionId'], c['meetingLocation']) for c in courses)
            for course in courses:
                section_id = course['sectionId']
                location = locations_per_section_id[section_id]
                if location != scheduled_rooms_per_section_id[int(section_id)]:
                    email_template = EmailTemplate.get_template_by_type('admin_alert_room_change')
                    send_email(
                        recipient_name='Course Capture Admin',
                        email_address=app.config['EMAIL_DIABLO_ADMIN'],
                        subject_line=interpolate_email_content(
                            templated_string=email_template.subject_line,
                            course=course,
                        ),
                        message=interpolate_email_content(
                            templated_string=email_template.message,
                            course=course,
                        ),
                    )


def _scheduled_locations_per_section_id(all_scheduled):
    locations_per_section_id = {}
    rooms = Room.get_rooms([s.room_id for s in all_scheduled])
    locations_per_room_id = dict((room.id, room.location) for room in rooms)
    for section_id, room_id in dict((s.section_id, s.room_id) for s in all_scheduled).items():
        locations_per_section_id[section_id] = locations_per_room_id[room_id]
    return locations_per_section_id
