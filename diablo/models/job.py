"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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
from diablo import db, std_commit
from diablo.lib.util import to_isoformat
from diablo.models.base import Base
from sqlalchemy.dialects.postgresql import ENUM


job_schedule_types = ENUM(
    'day_at',
    'minutes',
    'seconds',
    name='job_schedule_types',
    create_type=False,
)


class Job(Base):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    disabled = db.Column(db.Boolean, nullable=False)
    is_schedulable = db.Column(db.Boolean, nullable=False)
    job_schedule_type = db.Column(job_schedule_types, nullable=False)
    job_schedule_value = db.Column(db.String(80), nullable=False)
    key = db.Column(db.String(80), nullable=False, unique=True)

    def __init__(self, disabled, is_schedulable, job_schedule_type, job_schedule_value, key):
        self.disabled = disabled
        self.is_schedulable = is_schedulable
        self.job_schedule_type = job_schedule_type
        self.job_schedule_value = job_schedule_value
        self.key = key

    def __repr__(self):
        return f"""<Job
                    id={self.id},
                    disabled={self.disabled},
                    is_schedulable={self.is_schedulable},
                    job_schedule_type={self.job_schedule_type},
                    job_schedule_value={self.job_schedule_value},
                    key={self.key}>
                """

    @classmethod
    def create(cls, job_schedule_type, job_schedule_value, key, disabled=False, is_schedulable=True):
        job = cls(
            is_schedulable=is_schedulable,
            job_schedule_type=job_schedule_type,
            job_schedule_value=job_schedule_value,
            key=key,
            disabled=disabled,
        )
        db.session.add(job)
        std_commit()
        return job

    @classmethod
    def update_disabled(cls, job_id, disable):
        job = cls.query.filter_by(id=job_id).first()
        job.disabled = disable
        db.session.add(job)
        std_commit()
        return job

    @classmethod
    def update_schedule(cls, job_id, schedule_type, schedule_value):
        job = cls.query.filter_by(id=job_id).first()
        job.job_schedule_type = schedule_type
        job.job_schedule_value = schedule_value
        db.session.add(job)
        std_commit()
        return job

    @classmethod
    def get_all(cls, include_disabled=False):
        if include_disabled:
            return cls.query.order_by(cls.key).all()
        else:
            return cls.query.filter_by(disabled=False).order_by(cls.key).all()

    @classmethod
    def get_job(cls, job_id):
        return cls.query.filter_by(id=job_id).first()

    @classmethod
    def get_job_by_key(cls, key):
        return cls.query.filter_by(key=key).first()

    def to_api_json(self):
        return {
            'id': self.id,
            'disabled': self.disabled,
            'isSchedulable': self.is_schedulable,
            'key': self.key,
            'schedule': {
                'type': self.job_schedule_type,
                'value': int(self.job_schedule_value) if self.job_schedule_type in ['minutes', 'seconds'] else self.job_schedule_value,
            },
            'createdAt': to_isoformat(self.created_at),
            'updatedAt': to_isoformat(self.updated_at),
        }
