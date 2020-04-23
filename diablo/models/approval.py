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

from diablo import db, std_commit
from diablo.lib.util import to_isoformat
from diablo.models.room import Room
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY, ENUM


publish_type = ENUM(
    'canvas',
    'kaltura_media_gallery',
    name='publish_types',
    create_type=False,
)

recording_type = ENUM(
    'presentation_audio',
    'presenter_audio',
    'presenter_presentation_audio',
    name='recording_types',
    create_type=False,
)

approver_type = ENUM(
    'admin',
    'instructor',
    name='approver_types',
    create_type=False,
)

NAMES_PER_PUBLISH_TYPE = {
    'canvas': 'bCourses',
    'kaltura_media_gallery': 'My Media (Kaltura)',
}

NAMES_PER_RECORDING_TYPE = {
    'presentation_audio': 'Presentation and Audio',
    'presenter_audio': 'Presenter and Audio',
    'presenter_presentation_audio': 'Presenter, Presentation, and Audio',
}


class Approval(db.Model):
    __tablename__ = 'approvals'

    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    approved_by_uid = db.Column(db.String, nullable=False, primary_key=True)
    approver_type = db.Column(approver_type, nullable=False)
    cross_listed_section_ids = db.Column(ARRAY(db.Integer))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    publish_type = db.Column(publish_type, nullable=False)
    recording_type = db.Column(recording_type, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            term_id,
            section_id,
            approved_by_uid,
            approver_type_,
            cross_listed_section_ids,
            room_id,
            publish_type_,
            recording_type_,
    ):
        self.term_id = term_id
        self.section_id = section_id
        self.approved_by_uid = approved_by_uid
        self.approver_type = approver_type_
        self.cross_listed_section_ids = cross_listed_section_ids
        self.room_id = room_id
        self.publish_type = publish_type_
        self.recording_type = recording_type_

    def __repr__(self):
        return f"""<Approval
                    term_id={self.term_id},
                    section_id={self.section_id},
                    approved_by_uid={self.approved_by_uid},
                    approver_type={self.approver_type},
                    cross_listed_section_ids={self.cross_listed_section_ids}
                    publish_type={self.publish_type},
                    recording_type={self.recording_type},
                    room_id={self.room_id},
                    created_at={self.created_at}>
                """

    @classmethod
    def create(
            cls,
            term_id,
            section_id,
            approved_by_uid,
            approver_type_,
            cross_listed_section_ids,
            publish_type_,
            recording_type_,
            room_id,
    ):
        approval = cls(
            term_id=term_id,
            section_id=section_id,
            approved_by_uid=approved_by_uid,
            approver_type_=approver_type_,
            cross_listed_section_ids=cross_listed_section_ids,
            publish_type_=publish_type_,
            recording_type_=recording_type_,
            room_id=room_id,
        )
        db.session.add(approval)
        std_commit()
        return approval

    @classmethod
    def get_approval(cls, approved_by_uid, section_id, term_id):
        return cls.query.filter_by(approved_by_uid=approved_by_uid, section_id=section_id, term_id=term_id).first()

    @classmethod
    def get_approvals_per_section_ids(cls, section_ids, term_id):
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        return cls.query.filter(criteria).order_by(cls.created_at).all()

    @classmethod
    def get_approvals_per_term(cls, term_id):
        return cls.query.filter_by(term_id=int(term_id)).order_by(cls.section_id, cls.created_at).all()

    def to_api_json(self):
        return {
            'approvedByUid': self.approved_by_uid,
            'approverType': self.approver_type,
            'createdAt': to_isoformat(self.created_at),
            'crossListedSectionIds': self.cross_listed_section_ids,
            'publishType': self.publish_type,
            'publishTypeName': NAMES_PER_PUBLISH_TYPE[self.publish_type],
            'recordingType': self.recording_type,
            'recordingTypeName': NAMES_PER_RECORDING_TYPE[self.recording_type],
            'room': Room.get_room(self.room_id).to_api_json() if self.room_id else None,
            'sectionId': self.section_id,
            'termId': self.term_id,
        }


def get_all_publish_types():
    return publish_type.enums


def get_all_recording_types():
    return recording_type.enums
