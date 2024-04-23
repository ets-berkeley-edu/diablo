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
from itertools import groupby

from diablo import db, std_commit
from diablo.lib.util import to_isoformat
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM


schedule_update_status_type = ENUM(
    'queued',
    'succeeded',
    'errored',
    name='schedule_update_status_types',
    create_type=False,
)


class ScheduleUpdate(db.Model):
    __tablename__ = 'schedule_updates'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    term_id = db.Column(db.Integer, nullable=False)
    section_id = db.Column(db.Integer, nullable=False)
    field_name = db.Column(db.String, nullable=False)
    field_value_old = db.Column(db.String, nullable=True)
    field_value_new = db.Column(db.String, nullable=True)
    kaltura_schedule_id = db.Column(db.Integer, nullable=True)
    requested_by_uid = db.Column(db.String, nullable=True)
    requested_by_name = db.Column(db.String, nullable=True)
    status = db.Column(schedule_update_status_type)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    published_at = db.Column(db.DateTime, nullable=True)

    def __init__(
        self,
        term_id,
        section_id,
        field_name,
        field_value_old,
        field_value_new,
        kaltura_schedule_id,
        requested_by_uid,
        requested_by_name,
        status,
    ):
        self.term_id = term_id
        self.section_id = section_id
        self.field_name = field_name
        self.field_value_old = field_value_old
        self.field_value_new = field_value_new
        self.kaltura_schedule_id = kaltura_schedule_id
        self.requested_by_uid = requested_by_uid
        self.requested_by_name = requested_by_name
        self.status = status

    def __repr__(self):
        return f"""<ScheduleUpdate
                    term_id={self.term_id},
                    section_id={self.section_id},
                    field_name={self.field_name},
                    field_value_old={self.field_value_old},
                    field_value_new={self.field_value_new},
                    kaltura_schedule_id={self.kaltura_schedule_id}.
                    requested_by_uid={self.requested_by_uid},
                    requested_by_name={self.requested_by_name},
                    status={self.status}>
                """

    @classmethod
    def queue(
        cls,
        term_id,
        section_id,
        field_name,
        field_value_old,
        field_value_new,
        kaltura_schedule_id=None,
        requested_by_uid=None,
        requested_by_name=None,
    ):
        schedule_update = cls(
            term_id=term_id,
            section_id=section_id,
            field_name=field_name,
            field_value_old=field_value_old,
            field_value_new=field_value_new,
            kaltura_schedule_id=kaltura_schedule_id,
            requested_by_uid=requested_by_uid,
            requested_by_name=requested_by_name,
            status='queued',
        )
        db.session.add(schedule_update)
        std_commit()
        return schedule_update

    @classmethod
    def get_queued_by_section_id(cls, term_id=term_id):
        results = cls.query.filter_by(term_id=term_id, status='queued').order_by(cls.section_id, cls.requested_at).all()
        results_by_section_id = {}
        for section_id, section_results in groupby(results, lambda r: r.section_id):
            results_by_section_id[section_id] = list(section_results)
        return results_by_section_id

    @classmethod
    def get_section_history(cls, term_id=term_id, section_id=section_id):
        return cls.query.filter_by(term_id=term_id, section_id=section_id).order_by(cls.requested_at).all()

    @classmethod
    def find_collaborator_added(cls, term_id, section_id, collaborator_uid):
        sql = """
            SELECT * FROM schedule_updates
            WHERE term_id = :term_id
            AND section_id = :section_id
            AND field_name = 'collaborator_uids'
            AND NOT :collaborator_uid = ANY(field_value_old::varchar[])
            AND :collaborator_uid = ANY(field_value_new::varchar[])
            AND requested_by_uid IS NOT NULL
            AND status = 'succeeded'"""
        return db.session.execute(
            text(sql),
            {
                'collaborator_uid': collaborator_uid,
                'section_id': section_id,
                'term_id': term_id,
            },
        )

    @classmethod
    def find_collaborator_removed(cls, term_id, section_id, collaborator_uid):
        sql = """
            SELECT * FROM schedule_updates
            WHERE term_id = :term_id
            AND section_id = :section_id
            AND field_name = 'collaborator_uids'
            AND :collaborator_uid = ANY(field_value_old::varchar[])
            AND NOT :collaborator_uid = ANY(field_value_new::varchar[])
            AND requested_by_uid IS NOT NULL
            AND status = 'succeeded'"""
        return db.session.execute(
            text(sql),
            {
                'collaborator_uid': collaborator_uid,
                'section_id': section_id,
                'term_id': term_id,
            },
        )

    def mark_success(self):
        self.status = 'succeeded'
        self.published_at = datetime.now()
        db.session.add(self)
        std_commit()

    def mark_error(self):
        self.status = 'errored'
        self.published_at = datetime.now()
        db.session.add(self)
        std_commit()

    def to_api_json(self):
        return {
            'id': self.id,
            'termId': self.term_id,
            'sectionId': self.section_id,
            'fieldName': self.field_name,
            'fieldValueOld': self.field_value_old,
            'fieldValueNew': self.field_value_new,
            'kalturaScheduleId': self.kaltura_schedule_id,
            'requestedByUid': self.requested_by_uid,
            'requestedByName': self.requested_by_name,
            'status': self.status,
            'requestedAt': to_isoformat(self.requested_at),
            'publishedAt': to_isoformat(self.published_at),
        }
