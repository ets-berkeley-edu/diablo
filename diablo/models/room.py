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
from diablo.lib.util import to_isoformat
from diablo.models.course_preference import NAMES_PER_RECORDING_TYPE
from flask import current_app as app
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import ENUM


room_capability_type = ENUM(
    'screencast_and_video',
    name='room_capability_types',
    create_type=False,
)


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    capability = db.Column(room_capability_type)
    is_auditorium = db.Column(db.Boolean, nullable=False)
    kaltura_resource_id = db.Column(db.Integer)
    location = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            capability,
            is_auditorium,
            kaltura_resource_id,
            location,
    ):
        self.capability = capability
        self.is_auditorium = is_auditorium
        self.kaltura_resource_id = kaltura_resource_id
        self.location = location

    def __repr__(self):
        return f"""<Room
                    id={self.id},
                    capability={self.capability},
                    location={self.location},
                    is_auditorium={self.is_auditorium},
                    kaltura_resource_id={self.kaltura_resource_id},
                    created_at={self.created_at}>
                """

    @classmethod
    def create(cls, location, is_auditorium=False, kaltura_resource_id=None, capability=None):
        room = cls(
            capability=capability,
            is_auditorium=is_auditorium,
            kaltura_resource_id=kaltura_resource_id,
            location=location,
        )
        db.session.add(room)
        std_commit()
        return room

    @classmethod
    def find_room(cls, location):
        return cls.query.filter_by(location=location).first()

    @classmethod
    def get_eligible_rooms(cls):
        return cls.query.filter(cls.capability != None).all()  # noqa: E711

    @classmethod
    def get_room(cls, room_id):
        return cls.query.filter_by(id=room_id).first()

    @classmethod
    def get_rooms(cls, room_ids):
        return cls.query.filter(cls.id.in_(room_ids)).all()

    @classmethod
    def get_rooms_in_locations(cls, locations):
        return cls.query.filter(cls.location.in_(locations)).all()

    @classmethod
    def all_rooms(cls):
        return cls.query.order_by(cls.capability, cls.location).all()

    @classmethod
    def auditoriums(cls):
        return cls.query.filter_by(is_auditorium=True).order_by(cls.capability, cls.location).all()

    @classmethod
    def total_room_count(cls):
        return db.session.query(func.count(cls.id)).scalar()

    @classmethod
    def get_all_locations(cls):
        result = db.session.execute(text('SELECT location FROM rooms'))
        return [row['location'] for row in result]

    @classmethod
    def get_room_id(cls, section_id, term_id):
        sql = """
            SELECT r.id AS room_id
            FROM rooms r
            JOIN sis_sections s ON s.meeting_location = r.location
            WHERE s.section_id = :section_id AND s.term_id = :term_id
        """
        rows = db.session.execute(
            text(sql),
            {
                'section_id': section_id,
                'term_id': term_id,
            },
        )
        ids_ = [row['room_id'] for row in rows]
        return ids_[0] if ids_ else None

    @classmethod
    def update_capability(cls, room_id, capability):
        room = cls.query.filter_by(id=room_id).first()
        room.capability = capability
        db.session.add(room)
        std_commit()
        return room

    @classmethod
    def update_kaltura_resource_mappings(cls, kaltura_resource_ids_per_room):
        # First, set kaltura_resource_id = null on all rows
        cls.query.update({cls.kaltura_resource_id: None})
        # Next, insert the latest mappings
        all_rooms_per_id = dict((room.id, room) for room in cls.all_rooms())
        for room_id, kaltura_resource_id in kaltura_resource_ids_per_room.items():
            room = all_rooms_per_id[room_id]
            room.kaltura_resource_id = kaltura_resource_id
            db.session.add(room)
        std_commit()

    @classmethod
    def set_auditorium(cls, room_id, is_auditorium):
        room = cls.query.filter_by(id=room_id).first()
        room.is_auditorium = is_auditorium
        db.session.add(room)
        std_commit()
        return room

    @classmethod
    def get_room_capability_options(cls):
        return {
            'screencast_and_video': 'Screencast + Video',
        }

    def to_api_json(self):
        recording_type_options = {}

        def _add_recording_type(key):
            recording_type_options[key] = NAMES_PER_RECORDING_TYPE[key]

        _add_recording_type('presenter_presentation_audio')

        if self.is_auditorium:
            _add_recording_type('presenter_presentation_audio_with_operator')
            if app.config['COURSE_CAPTURE_PREMIUM_COST']:
                recording_type_options['presenter_presentation_audio_with_operator'] += f" (${app.config['COURSE_CAPTURE_PREMIUM_COST']})"

        return {
            'id': self.id,
            'location': self.location,
            'capability': self.capability,
            'capabilityName': self.get_room_capability_options()[self.capability] if self.capability else None,
            'createdAt': to_isoformat(self.created_at),
            'isAuditorium': self.is_auditorium,
            'kalturaResourceId': self.kaltura_resource_id,
            'recordingTypeOptions': recording_type_options,
        }
