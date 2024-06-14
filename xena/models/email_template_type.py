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

    ADMIN_OPERATOR_REQUESTED = {
        # TODO 'desc': '',
        'type': 'admin_operator_requested',
    }
    INSTR_ADDED = {
        # TODO 'desc': '',
        'type': 'instructors_added',
    }
    INSTR_ANNUNCIATION_NEW_COURSE_SCHED = {
        # TODO 'desc': '',
        'type': 'new_class_scheduled',
    }
    INSTR_ANNUNCIATION_REMINDER = {
        # TODO 'desc': '',
        'type': 'remind_scheduled',
    }
    INSTR_ANNUNCIATION_SEM_START = {
        # TODO 'desc': '',
        'type': 'semester_start',
    }
    INSTR_CHANGES_CONFIRMED = {
        # TODO 'desc': '',
        'type': 'changes_confirmed',
    }
    INSTR_COURSE_CANCELLED = {
        # TODO 'desc': '',
        'type': 'no_longer_scheduled',
    }
    INSTR_OPTED_OUT = {
        # TODO 'desc': '',
        'type': 'opted_out',
    }
    INSTR_REMOVED = {
        # TODO 'desc': '',
        'type': 'instructors_removed',
    }
    INSTR_ROOM_CHANGE_INELIGIBLE = {
        # TODO 'desc': '',
        'type': 'room_change_no_longer_eligible',
    }
    INSTR_SCHEDULE_CHANGE = {
        # TODO 'desc': '',
        'type': 'schedule_change',
    }
