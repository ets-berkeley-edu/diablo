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
from diablo.lib.util import format_days, format_time, to_isoformat
from diablo.models.room import Room
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY


class Scheduled(db.Model):
    __tablename__ = 'scheduled'

    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    instructor_uids = db.Column(ARRAY(db.String(80)), nullable=False)
    meeting_days = db.Column(db.String, nullable=False)
    meeting_start_time = db.Column(db.String, nullable=False)
    meeting_end_time = db.Column(db.String, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(
            self,
            section_id,
            term_id,
            instructor_uids,
            meeting_days,
            meeting_start_time,
            meeting_end_time,
            room_id,
    ):
        self.section_id = section_id
        self.term_id = term_id
        self.instructor_uids = instructor_uids
        self.meeting_days = meeting_days
        self.meeting_start_time = meeting_start_time
        self.meeting_end_time = meeting_end_time
        self.room_id = room_id

    def __repr__(self):
        return f"""<Scheduled
                    section_id={self.section_id},
                    term_id={self.term_id},
                    instructor_uids={', '.join(self.instructor_uids)},
                    meeting_days={self.meeting_days},
                    meeting_start_time={self.meeting_start_time},
                    meeting_end_time={self.meeting_end_time},
                    room_id={self.room_id},
                    created_at={self.created_at}>
                """

    @classmethod
    def create(
            cls,
            section_id,
            term_id,
            instructor_uids,
            meeting_days,
            meeting_start_time,
            meeting_end_time,
            room_id,
    ):
        scheduled = cls(
            section_id=section_id,
            term_id=term_id,
            instructor_uids=instructor_uids,
            meeting_days=meeting_days,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            room_id=room_id,
        )
        db.session.add(scheduled)
        std_commit()
        return scheduled

    @classmethod
    def get_all_scheduled(cls, term_id):
        return cls.query.filter_by(term_id=term_id).all()

    @classmethod
    def get_scheduled_per_section_ids(cls, section_ids, term_id):
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        return cls.query.filter(criteria).order_by(cls.created_at).all()

    @classmethod
    def get_scheduled(cls, section_id, term_id):
        return cls.query.filter_by(section_id=section_id, term_id=term_id).first()

    def to_api_json(self):
        return {
            'sectionId': self.section_id,
            'termId': self.term_id,
            'instructorUids': self.instructor_uids,
            'meetingDays': format_days(self.meeting_days),
            'meetingEndTime': format_time(self.meeting_end_time),
            'meetingStartTime': format_time(self.meeting_start_time),
            'room': Room.get_room(self.room_id).to_api_json() if self.room_id else None,
            'createdAt': to_isoformat(self.created_at),
        }
