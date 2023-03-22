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
from diablo.jobs.base_job import BaseJob
from diablo.models.approval import Approval
from diablo.models.queued_email import QueuedEmail
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app


class RemindInviteesJob(BaseJob):

    def _run(self):
        term_id = app.config['CURRENT_TERM_ID']
        courses = SisSection.get_courses(term_id=term_id)
        section_ids = list(set([c['sectionId'] for c in courses]))
        approvals_by_section_id = _get_approvals_by_section_id(
            section_ids=section_ids,
            term_id=term_id,
        )
        invitation_recipient_uids = _get_invitation_recipient_uids(
            section_ids=section_ids,
            term_id=term_id,
        )
        scheduled_by_section_id = {s.section_id: s for s in Scheduled.get_all_scheduled(term_id=term_id)}
        for course in courses:
            section_id = course['sectionId']
            if section_id not in scheduled_by_section_id:
                if not course['hasOptedOut'] and len(course.get('meetings', {}).get('eligible', [])) >= 1:
                    approvals = approvals_by_section_id.get(section_id) or []
                    approved_by_uids = [a.approved_by_uid for a in approvals]
                    for i in course['instructors']:
                        uid = i['uid']
                        if uid not in approved_by_uids and uid in invitation_recipient_uids:
                            QueuedEmail.create(
                                recipient=i,
                                section_id=section_id,
                                template_type='remind_invitees',
                                term_id=term_id,
                            )

    @classmethod
    def description(cls):
        return 'Queues up reminder emails for invitees who have not RSVPed.'

    @classmethod
    def key(cls):
        return 'remind_invitees'


def _get_approvals_by_section_id(section_ids, term_id):
    approvals_by_section_id = {}
    for approval in Approval.get_approvals_per_section_ids(section_ids=section_ids, term_id=term_id):
        section_id = approval.section_id
        if section_id not in approvals_by_section_id:
            approvals_by_section_id[section_id] = []
        approvals_by_section_id[section_id].append(approval)
    return approvals_by_section_id


def _get_invitation_recipient_uids(section_ids, term_id):
    sent_emails = SentEmail.get_emails_of_type(
        section_ids=section_ids,
        template_type='invitation',
        term_id=term_id,
    )
    recipient_uids = [e.recipient_uid for e in sent_emails]
    # Queued email
    for queued_email in QueuedEmail.get_all(term_id=term_id):
        if queued_email.template_type == 'invitation' and queued_email.section_id in section_ids:
            if 'uid' in queued_email.recipient:
                recipient_uids.append(queued_email.recipient['uid'])
    return recipient_uids
