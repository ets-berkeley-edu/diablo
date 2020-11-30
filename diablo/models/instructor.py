"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

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

from diablo import db
from diablo.lib.util import utc_now
from diablo.models.base import Base


class Instructor(Base):
    __tablename__ = 'instructors'

    uid = db.Column(db.String(255), primary_key=True)
    dept_code = db.Column(db.String(80))
    email = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))

    def __init__(
            self,
            dept_code,
            email,
            first_name,
            last_name,
            uid,
    ):
        self.dept_code = dept_code
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.uid = uid

    def __repr__(self):
        return f"""<Instructor
                    dept_code={', '.join(self.dept_code)},
                    email={self.email},
                    first_name={self.first_name},
                    last_name={self.last_name},
                    uid={self.uid},
                    created_at={self.created_at},
                    updated_at={self.updated_at}>
                """

    @classmethod
    def upsert(cls, rows):
        now = utc_now().strftime('%Y-%m-%dT%H:%M:%S+00')
        count_per_chunk = 10000
        for chunk in range(0, len(rows), count_per_chunk):
            rows_subset = rows[chunk:chunk + count_per_chunk]
            query = """
                INSERT INTO instructors (
                    created_at, dept_code, email, first_name, last_name, uid, updated_at
                )
                SELECT
                    created_at, dept_code, email, first_name, last_name, uid, updated_at
                FROM json_populate_recordset(null::instructors, :json_dumps)
                ON CONFLICT(uid) DO
                UPDATE SET
                    dept_code = EXCLUDED.dept_code,
                    email = EXCLUDED.email,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name;
            """
            data = [
                {
                    'created_at': now,
                    'dept_code': row['dept_code'],
                    'email': row['email'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'uid': row['uid'],
                    'updated_at': now,
                } for row in rows_subset
            ]
            db.session.execute(query, {'json_dumps': json.dumps(data)})
