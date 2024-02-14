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
from sqlalchemy import and_, text
from sqlalchemy.sql import desc


class JobHistory(db.Model):
    __tablename__ = 'job_history'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    job_key = db.Column(db.String(80), nullable=False)
    failed = db.Column(db.Boolean, nullable=False, default=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    finished_at = db.Column(db.DateTime)

    def __init__(self, job_key):
        self.job_key = job_key
        self.failed = False
        self.started_at = datetime.now()

    def __repr__(self):
        return f"""<Room
                    id={self.id},
                    job_key={self.job_key},
                    failed={self.failed},
                    started_at={self.started_at},
                    finished_at={self.finished_at},
                """

    @classmethod
    def is_job_running(cls, job_key):
        return cls.query.filter_by(job_key=job_key, finished_at=None).first() is not None

    @classmethod
    def job_started(cls, job_key):
        row = cls(job_key=job_key)
        db.session.add(row)
        std_commit()
        return row

    @classmethod
    def job_finished(cls, id_, failed=False):
        row = cls.query.filter_by(id=id_).first()
        row.failed = failed
        row.finished_at = datetime.now()
        db.session.add(row)
        std_commit()
        return row

    @classmethod
    def get_job_history(cls):
        return cls.query.order_by(desc(cls.started_at)).all()

    @classmethod
    def last_successful_run_of(cls, job_key):
        criteria = and_(cls.job_key == job_key, cls.failed == False, cls.finished_at != None)  # noqa: E711, E712
        return cls.query.filter(criteria).order_by(desc(cls.finished_at)).limit(1).first()

    @staticmethod
    def fail_orphans():
        sql = """
            UPDATE job_history
            SET failed = TRUE, finished_at = now()
            WHERE finished_at IS NULL"""
        db.session.execute(text(sql))

    @staticmethod
    def expire_old_rows(days):
        sql = f"DELETE FROM job_history WHERE started_at < (now() - INTERVAL '{days} DAYS')"
        db.session.execute(text(sql))

    def to_api_json(self):
        return {
            'id': self.id,
            'jobKey': self.job_key,
            'failed': self.failed,
            'startedAt': to_isoformat(self.started_at),
            'finishedAt': self.finished_at and to_isoformat(self.finished_at),
        }
