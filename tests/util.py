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

from contextlib import contextmanager

from diablo.models.approval import Approval
from diablo.models.room import Room
from diablo.models.scheduled import Scheduled
from sqlalchemy import text


@contextmanager
def override_config(app, key, value):
    """Temporarily override an app config value."""
    old_value = app.config[key]
    app.config[key] = value
    try:
        yield
    finally:
        app.config[key] = old_value


@contextmanager
def create_approvals_and_scheduled(db, location):
    Room.create_or_update(
        location='Barrows 106',
        capabilities='Screencast',
    )
    section_ids = [30563, 26094]
    term_id = 2202
    uids = ['234567', '1015674']

    Approval.create(
        approved_by_uid=uids[0],
        term_id=term_id,
        section_id=section_ids[0],
        approver_type_='instructor',
        publish_type_='canvas',
        recording_type_='presentation_audio',
        location=location,
    )
    Approval.create(
        approved_by_uid=uids[1],
        term_id=term_id,
        section_id=section_ids[1],
        approver_type_='admin',
        publish_type_='kaltura_media_gallery',
        recording_type_='presenter_audio',
        location=location,
    )
    Scheduled.create(
        term_id=term_id,
        section_id='26094',
        location=location,
    )
    try:
        yield
    finally:
        for index in range(0, 2):
            db.session.execute(
                text('DELETE FROM approvals WHERE section_id = :section_id AND term_id = :term_id AND approved_by_uid = :uid'),
                {
                    'section_id': section_ids[index],
                    'term_id': term_id,
                    'uid': uids[index],
                },
            )
