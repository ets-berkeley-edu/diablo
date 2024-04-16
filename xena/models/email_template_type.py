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

from enum import Enum


class EmailTemplateType(Enum):

    ADMIN_DATE_CHANGE = {
        'desc': 'Admin alert: Date change',
        'type': 'admin_alert_date_change',
    }
    ADMIN_INSTR_CHANGE = {
        'desc': 'Admin alert: Instructor change',
        'type': 'admin_alert_instructor_change',
    }
    ADMIN_ROOM_CHANGE = {
        'desc': 'Admin alert: Room change',
        'type': 'admin_alert_room_change',
    }
    ADMIN_WEIRD_DATES = {
        'desc': 'Admin alert: Weird start/end dates',
        'type': 'admin_alert_multiple_meeting_patterns',
    }
    INSTR_AWAITING_APPROVAL = {
        'desc': 'Waiting for approval',
        'type': 'waiting_for_approval',
    }
    INSTR_ANNUNCIATION = {
        'desc': 'Announcement',
        'type': 'announcement',
    }
    INSTR_ANNUNCIATION_REMINDER = {
        'desc': 'Remind Scheduled',
        'type': 'remind_scheduled',
    }
    INSTR_RECORDINGS_SCHEDULED = {
        'desc': 'Recordings scheduled',
        'type': 'recordings_scheduled',
    }
    INSTR_ROOM_CHANGE_INELIGIBLE = {
        'desc': 'Room change: No longer eligible',
        'type': 'room_change_no_longer_eligible',
    }
    INSTR_CHANGES_CONFIRMED = {
        'desc': 'Changes confirmed',
        'type': 'changes_confirmed',
    }
