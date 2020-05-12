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

import json

from config import xena
from diablo import db, std_commit
from flask import current_app as app
from sqlalchemy import text
from xena.models.room import Room


def get_xena_browser():
    return xena.XENA_BROWSER


def get_short_timeout():
    return xena.TIMEOUT_SHORT


def get_long_timeout():
    return xena.TIMEOUT_LONG


def get_admin_uid():
    return xena.ADMIN_UID


def parse_rooms_data():
    with open(xena.TEST_DATA_ROOMS) as f:
        parsed = json.load(f)
        return [Room(agent) for agent in parsed['agents']]


def parse_sign_up_test_data():
    with open(xena.TEST_DATA_SIGNUP) as f:
        parsed = json.load(f)
        return parsed['courses']


def reset_test_data(course_data):
    ccn = course_data['ccn']
    term = app.config['CURRENT_TERM_ID']
    sql = f'DELETE FROM approvals WHERE section_id = {ccn} AND term_id = {term}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM scheduled WHERE section_id = {ccn} AND term_id = {term}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM sent_emails WHERE section_id = {ccn} AND term_id = {term}'
    db.session.execute(text(sql))
    sql = f'DELETE FROM course_preferences WHERE section_id = {ccn} AND term_id = {term}'
    db.session.execute(text(sql))
    std_commit(allow_test_environment=True)
