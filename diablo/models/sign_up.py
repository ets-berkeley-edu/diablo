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
from diablo.models.base import Base
from sqlalchemy.dialects.postgresql import ARRAY, ENUM


publish_type = ENUM(
    'canvas',
    'kaltura_media_gallery',
    name='publish_types',
    create_type=False,
)

recording_type = ENUM(
    'presentation_audio',
    'presenter_audio'
    'presenter_presentation_audio',
    name='recording_types',
    create_type=False,
)


class SignUp(Base):
    __tablename__ = 'sign_ups'

    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    admin_approval_uid = db.Column(db.String)
    instructor_approval_uids = db.Column(ARRAY(db.String))
    publish_type = db.Column(publish_type, nullable=False)
    recording_type = db.Column(recording_type, nullable=False)
    requires_multiple_approvals = db.Column(db.Boolean, nullable=False)

    def __init__(
            self,
            term_id,
            section_id,
            admin_approval_uid,
            instructor_approval_uids,
            publish_type_,
            recording_type_,
            requires_multiple_approvals,
    ):
        self.term_id = term_id
        self.section_id = section_id
        self.admin_approval_uid = admin_approval_uid
        self.instructor_approval_uids = instructor_approval_uids
        self.publish_type = publish_type_
        self.recording_type = recording_type_
        self.requires_multiple_approvals = requires_multiple_approvals

    def __repr__(self):
        return f"""<SignUp
                    term_id={self.term_id},
                    section_id={self.section_id},
                    admin_approval_uid={self.admin_approval_uid},
                    instructor_approval_uids={self.instructor_approval_uids},
                    publish_type={self.publish_type},
                    recording_type={self.recording_type},
                    requires_multiple_approvals={self.requires_multiple_approvals},
                    created_at={self.created_at},
                    updated_at={self.updated_at}>
                """

    @classmethod
    def get_sign_up(cls, term_id, section_id):
        return cls.query.filter_by(term_id=term_id, section_id=section_id).first()

    @classmethod
    def get_all_sign_ups(cls, term_id):
        return cls.query.filter_by(term_id=term_id).first()

    def to_api_json(self):
        return {
            'termId': self.term_id,
            'sectionId': self.section_id,
            'adminApprovalUid': self.admin_approval_uid,
            'instructorApprovalUids': self.instructor_approval_uids,
            'publishType': self.publish_type,
            'recordingType': self.recording_type,
            'requiresMultipleApprovals': self.requires_multiple_approvals,
        }
