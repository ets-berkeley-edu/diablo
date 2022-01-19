"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

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
from sqlalchemy import and_


class CanvasCourseSite(db.Model):
    __tablename__ = 'canvas_course_sites'

    canvas_course_site_id = db.Column(db.Integer, nullable=False, primary_key=True)
    section_id = db.Column(db.Integer, nullable=False, primary_key=True)
    term_id = db.Column(db.Integer, nullable=False, primary_key=True)
    canvas_course_site_name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, canvas_course_site_id, section_id, term_id, canvas_course_site_name):
        self.canvas_course_site_id = canvas_course_site_id
        self.section_id = section_id
        self.term_id = term_id
        self.canvas_course_site_name = canvas_course_site_name

    def __repr__(self):
        return f"""<CanvasCourseSite
                    canvas_course_site_id={self.canvas_course_site_id}
                    canvas_course_site_name={self.canvas_course_site_name}
                    section_id={self.section_id},
                    term_id={self.term_id},
                    created_at={self.created_at}
                """

    @classmethod
    def get_all_canvas_course_sites(cls, term_id):
        return cls.query.filter_by(term_id=term_id).all()

    @classmethod
    def get_canvas_course_sites(cls, section_ids, term_id):
        criteria = and_(cls.section_id.in_(section_ids), cls.term_id == term_id)
        return cls.query.filter(criteria).all()

    @classmethod
    def refresh_term_data(cls, term_id, canvas_course_sites):
        db.session.execute(cls.__table__.delete().where(cls.term_id == term_id))
        for canvas_course_site in canvas_course_sites:
            for section_id in canvas_course_site['section_ids']:
                db.session.add(
                    cls(
                        canvas_course_site_id=canvas_course_site['id'],
                        section_id=section_id,
                        term_id=term_id,
                        canvas_course_site_name=canvas_course_site['name'],
                    ),
                )
        std_commit()

    def to_api_json(self):
        return {
            'canvasCourseSiteId': self.canvas_course_site_id,
            'canvasCourseSiteName': self.canvas_course_site_name,
            'sectionId': self.section_id,
            'termId': self.term_id,
            'createdAt': to_isoformat(self.created_at),
        }
