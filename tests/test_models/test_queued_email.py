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
from diablo.models.queued_email import QueuedEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app


class TestQueuedEmail:

    def test_currently_no_person_teaching_course(self):
        """Refuse to queue emails for a course without a proper instructor."""
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50006
        email_template_type = 'invitation'
        # Courses with no proper instructor are excluded from query results.
        assert not SisSection.get_course(term_id=term_id, section_id=section_id)

        # Queued email creation fails.
        assert not QueuedEmail.create(section_id, email_template_type, term_id, recipient=None)
        assert section_id not in QueuedEmail.get_all_section_ids(template_type=email_template_type, term_id=term_id)

    def test_no_email_template_available(self):
        """Refuse to queue emails if no template is available."""
        term_id = app.config['CURRENT_TERM_ID']
        section_id = 50005
        email_template_type = 'waiting_for_approval'
        recipient = {
            'name': 'Regan MacNeil',
            'uid': '10006',
        }
        # Queued email creation fails.
        assert not QueuedEmail.create(section_id, email_template_type, term_id, recipient=recipient)
        assert section_id not in QueuedEmail.get_all_section_ids(template_type=email_template_type, term_id=term_id)
