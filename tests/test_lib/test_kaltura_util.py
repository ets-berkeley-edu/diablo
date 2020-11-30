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
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.kaltura_util import get_classification_name, get_recurrence_name, get_series_description, \
    get_status_name
from diablo.models.sis_section import SisSection
from flask import current_app as app
from KalturaClient.Plugins.Schedule import KalturaScheduleEventClassificationType, KalturaScheduleEventRecurrenceType, \
    KalturaScheduleEventStatus


class TestKalturaEnums:

    def test_classification_name(self):
        """Friendly name for KalturaScheduleEventClassificationType enum values."""
        assert get_classification_name(None) is None
        assert get_classification_name(
            KalturaScheduleEventClassificationType(KalturaScheduleEventClassificationType.PUBLIC_EVENT),
        ) == 'Public'

    def test_recurrence_name(self):
        """Friendly name for KalturaScheduleEventRecurrenceType enum values."""
        assert get_recurrence_name(None) is None
        assert get_recurrence_name(
            KalturaScheduleEventRecurrenceType(KalturaScheduleEventRecurrenceType.RECURRING),
        ) == 'Recurring'

    def test_status_name(self):
        """Friendly name for KalturaScheduleEventStatus enum values."""
        assert get_status_name(None) is None
        assert get_status_name(
            KalturaScheduleEventStatus(KalturaScheduleEventStatus.ACTIVE),
        ) == 'Active'

    def test_series_description(self):
        """Series description for cross-listed course."""
        cross_listed_section_id = 50012
        term_id = app.config['CURRENT_TERM_ID']
        course = SisSection.get_course(
            section_id=cross_listed_section_id,
            term_id=term_id,
        )
        description = get_series_description(
            course_label=course['label'],
            instructors=course['instructors'],
            term_name=term_name_for_sis_id(term_id),
        )
        assert 'MATH C51, LEC 001 | STAT C151, COL 001' in description
        assert 'Fall 2020' in description
        assert 'Rudolf Schündler and Arthur Storch' in description
        assert '2020' in description
