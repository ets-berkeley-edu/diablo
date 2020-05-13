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
from diablo.models.email_template import email_template_type, EmailTemplate
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY


class SentEmail(db.Model):
    __tablename__ = 'sent_emails'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    recipient_uids = db.Column(ARRAY(db.String(80)), nullable=False)
    section_id = db.Column(db.Integer)
    template_type = db.Column(email_template_type)
    term_id = db.Column(db.Integer, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, recipient_uids, section_id, template_type, term_id):
        self.recipient_uids = recipient_uids
        self.template_type = template_type
        self.section_id = section_id
        self.term_id = term_id

    def __repr__(self):
        return f"""<SentEmail
                    id={self.id}
                    recipient_uids={', '.join(self.recipient_uids)}
                    section_id={self.section_id},
                    template_type={self.template_type}
                    term_id={self.term_id},
                    sent_at={self.sent_at}
                """

    @classmethod
    def create(cls, recipient_uids, section_id, template_type, term_id):
        sent_email = cls(
            recipient_uids=recipient_uids,
            section_id=section_id,
            template_type=template_type,
            term_id=term_id,
        )
        db.session.add(sent_email)
        std_commit()
        return sent_email

    @classmethod
    def get_emails_sent_to(cls, uid):
        return cls.query.filter(cls.recipient_uids.any(uid)).order_by(cls.sent_at).all()

    @classmethod
    def get_emails_of_type(cls, section_ids, template_type, term_id):
        criteria = and_(cls.section_id.in_(section_ids), cls.template_type == template_type, cls.term_id == term_id)
        return cls.query.filter(criteria).order_by(cls.sent_at).all()

    def to_api_json(self):
        return {
            'id': self.id,
            'recipientUids': self.recipient_uids,
            'sectionId': self.section_id,
            'templateType': self.template_type,
            'templateTypeName': EmailTemplate.get_template_type_options()[self.template_type],
            'termId': self.term_id,
            'sentAt': to_isoformat(self.sent_at),
        }
