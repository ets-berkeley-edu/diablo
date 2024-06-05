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

from diablo import db, std_commit
from diablo.externals.loch import get_loch_basic_attributes
from diablo.lib.util import basic_attributes_to_api_json, to_isoformat
from diablo.models.cross_listing import CrossListing
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY, ENUM


publish_type = ENUM(
    'kaltura_media_gallery',
    'kaltura_media_gallery_moderated',
    'kaltura_my_media',
    name='publish_types',
    create_type=False,
)


# In addition to these active options, legacy data includes the deprecated 'presentation_audio' and 'presenter_audio' options.
recording_type = ENUM(
    'presenter_presentation_audio',
    'presenter_presentation_audio_with_operator',
    name='recording_types',
    create_type=False,
)


NAMES_PER_PUBLISH_TYPE = {
    'kaltura_media_gallery': 'Publish Automatically to Course Site',
    'kaltura_media_gallery_moderated': 'Publish to Pending Tab in Course Site',
    'kaltura_my_media': 'Publish to My Media',
}


NAMES_PER_RECORDING_TYPE = {
    'presenter_presentation_audio': 'Camera without Operator',
    'presenter_presentation_audio_with_operator': 'Camera with Operator',
}


class CoursePreference(db.Model):
    __tablename__ = 'course_preferences'

    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    collaborator_uids = db.Column(ARRAY(db.String(80)))
    publish_type = db.Column(publish_type, nullable=False)
    recording_type = db.Column(recording_type, nullable=False)
    canvas_site_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            term_id,
            section_id,
            publish_type='kaltura_my_media',
            recording_type='presenter_presentation_audio',
            canvas_site_id=None,
            collaborator_uids=None,
    ):
        self.term_id = term_id
        self.section_id = section_id
        self.publish_type = publish_type
        self.recording_type = recording_type
        self.canvas_site_id = canvas_site_id
        self.collaborator_uids = collaborator_uids

    def __repr__(self):
        return f"""<CoursePreferences
                    term_id={self.term_id},
                    section_id={self.section_id},
                    publish_type={self.publish_type}
                    recording_type={self.recording_type}
                    collaborator_uids={self.collaborator_uids}
                    canvas_site_id={self.canvas_site_id}
                    created_at={self.created_at}
                """

    @classmethod
    def get_all_course_preferences(cls, term_id):
        return cls.query.filter_by(term_id=term_id).all()

    @classmethod
    def get_course_preferences(cls, section_id, term_id):
        return cls.query.filter_by(section_id=section_id, term_id=term_id).first()

    @classmethod
    def update_collaborator_uids(
            cls,
            term_id,
            section_id,
            collaborator_uids,
    ):
        section_ids = _get_section_ids_with_xlistings(section_id, term_id)
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        for existing_row in cls.query.filter(criteria).all():
            existing_row.collaborator_uids = list(collaborator_uids)
            if existing_row.section_id in section_ids:
                section_ids.remove(existing_row.section_id)
        for section_id in section_ids:
            preferences = cls(
                term_id=term_id,
                section_id=section_id,
                collaborator_uids=collaborator_uids,
            )
            db.session.add(preferences)
        std_commit()
        return cls.query.filter_by(term_id=term_id, section_id=section_id).first()

    @classmethod
    def update_publish_type(
            cls,
            term_id,
            section_id,
            publish_type,
            canvas_site_id,
    ):
        section_ids = _get_section_ids_with_xlistings(section_id, term_id)
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        for existing_row in cls.query.filter(criteria).all():
            existing_row.publish_type = publish_type
            existing_row.canvas_site_id = canvas_site_id
            section_ids.remove(existing_row.section_id)
        for section_id in section_ids:
            preferences = cls(
                term_id=term_id,
                section_id=section_id,
                publish_type=publish_type,
                canvas_site_id=canvas_site_id,
            )
            db.session.add(preferences)
        std_commit()
        return cls.query.filter_by(term_id=term_id, section_id=section_id).first()

    @classmethod
    def update_recording_type(
            cls,
            term_id,
            section_id,
            recording_type,
    ):
        section_ids = _get_section_ids_with_xlistings(section_id, term_id)
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        for existing_row in cls.query.filter(criteria).all():
            existing_row.recording_type = recording_type
            section_ids.remove(existing_row.section_id)
        for section_id in section_ids:
            preferences = cls(
                term_id=term_id,
                section_id=section_id,
                recording_type=recording_type,
            )
            db.session.add(preferences)
        std_commit()
        return cls.query.filter_by(term_id=term_id, section_id=section_id).first()

    def get_collaborator_attributes(self):
        if self.collaborator_uids:
            return [basic_attributes_to_api_json(a) for a in get_loch_basic_attributes(self.collaborator_uids)]
        else:
            return []

    def to_api_json(self):
        return {
            'termId': self.term_id,
            'sectionId': self.section_id,
            'collaborators': self.get_collaborator_attributes(),
            'collaboratorUids': self.collaborator_uids,
            'publishType': self.publish_type,
            'publishTypeName': NAMES_PER_PUBLISH_TYPE[self.publish_type],
            'recordingType': self.recording_type,
            'recordingTypeName': NAMES_PER_RECORDING_TYPE[self.recording_type],
            'canvasSiteId': self.canvas_site_id,
            'createdAt': to_isoformat(self.created_at),
        }


def get_all_publish_types():
    return publish_type.enums


def get_all_recording_types():
    return recording_type.enums


def _get_section_ids_with_xlistings(section_id, term_id):
    return CrossListing.get_cross_listed_section_ids(section_id=section_id, term_id=term_id) + [section_id]
