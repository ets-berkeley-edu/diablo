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
from datetime import timedelta
import json
import time

from config import xena
from diablo import db, std_commit
from diablo.models.scheduled import Scheduled
from flask import current_app as app
from sqlalchemy import text
from xena.models.recording_schedule_status import RecordingScheduleStatus
from xena.models.room import Room


def get_xena_browser():
    return xena.XENA_BROWSER


def get_short_timeout():
    return xena.TIMEOUT_SHORT


def get_long_timeout():
    return xena.TIMEOUT_LONG


def get_admin_uid():
    return xena.ADMIN_UID


def get_kaltura_username():
    return xena.KALTURA_USERNAME


def get_kaltura_password():
    return xena.KALTURA_PASSWORD


def get_kaltura_term_date_str(date):
    return datetime.strftime(date, '%m/%d/%Y')


def parse_rooms_data():
    with open(xena.TEST_DATA_ROOMS) as f:
        parsed = json.load(f)
        return [Room(agent) for agent in parsed['agents']]


def parse_sign_up_test_data():
    with open(xena.TEST_DATA_SIGNUP) as f:
        parsed = json.load(f)
        return parsed['courses']


def wait_for_kaltura_id(recording_schedule, term):
    section = recording_schedule.section
    app.logger.info(f'Term {term.id} section {section.ccn}')
    tries = 0
    retries = 10
    while tries <= retries:
        tries += 1
        try:
            result = Scheduled.get_scheduled(section.ccn, term.id)
            app.logger.info(f'Result is {result}')
            app.logger.info(f'ID is {result.kaltura_schedule_id}')
            assert result
            recording_schedule.series_id = result.kaltura_schedule_id
            recording_schedule.status = RecordingScheduleStatus.SCHEDULED
            break
        except Exception:
            if tries == retries:
                raise
            else:
                time.sleep(get_short_timeout())


def reset_sign_up_test_data(course_data):
    ccn = course_data['ccn']
    term_id = app.config['CURRENT_TERM_ID']
    sql = f'DELETE FROM approvals WHERE section_id = {ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM scheduled WHERE section_id = {ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM sent_emails WHERE section_id = {ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM course_preferences WHERE section_id = {ccn} AND term_id = {term_id}'
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)


def get_next_date(start_date, day_index):
    days_ahead = day_index - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return start_date + timedelta(days_ahead)


def get_first_recording_date(recording_schedule):
    term_start_date = datetime.strptime(app.config['CURRENT_TERM_BEGIN'], '%Y-%m-%d')
    day_to_index = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4}
    schedule_days_str = recording_schedule.section.days.replace(' ', '').split(',')
    schedule_days_ind = [day_to_index[day] for day in schedule_days_str]
    next_dates = [get_next_date(term_start_date, index) for index in schedule_days_ind]
    next_dates.sort()
    return next_dates[0]


def reset_invite_test_data(term, section, instructor=None):
    # So that invitation will be sent to one instructor on a course
    if instructor:
        sql = f"""UPDATE sent_emails
                  SET recipient_uids = array_remove(recipient_uids, '{instructor.uid}')
                  WHERE term_id = {term.id}
                    AND section_id = {section.ccn}
                    AND template_type = 'invitation'
        """
    # So that invitations will be sent to all instructors on a course
    else:
        sql = f"""DELETE FROM sent_emails
                  WHERE term_id = {term.id}
                    AND section_id = {section.ccn}
                    AND template_type = 'invitation'
        """
    app.logger.info(sql)
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
