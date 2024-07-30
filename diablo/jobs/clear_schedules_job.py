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
from diablo.externals.kaltura import Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.models.scheduled import Scheduled
from diablo.models.sis_section import SisSection
from flask import current_app as app


class ClearSchedulesJob(BaseJob):

    def _run(self):
        kaltura = Kaltura()
        term_id = app.config['CURRENT_TERM_ID']
        for course in SisSection.get_courses_scheduled(term_id):
            for scheduled in course['scheduled'] or []:
                try:
                    kaltura.delete(scheduled['kalturaScheduleId'])
                    Scheduled.delete(term_id=term_id, section_id=course['sectionId'], kaltura_schedule_id=scheduled['kalturaScheduleId'])
                except Exception as e:
                    app.logger.error(
                        f"Failed to delete Kaltura schedule: term {term_id}, section {course['sectionId']},"
                        f" Kaltura schedule {scheduled['kalturaScheduleId']}")
                    app.logger.exception(e)

    @classmethod
    def description(cls):
        return 'Deletes all Course Capture (Kaltura) schedules for the current term.'

    @classmethod
    def key(cls):
        return 'clear_schedules'
