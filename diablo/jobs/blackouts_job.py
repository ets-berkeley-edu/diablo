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
from diablo.externals.kaltura import CREATED_BY_DIABLO_TAG, Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.lib.kaltura_util import represents_recording_series
from diablo.lib.util import localize_datetime, utc_now
from diablo.models.blackout import Blackout
from flask import current_app as app
from KalturaClient.Plugins.Schedule import KalturaScheduleEventRecurrenceType


class BlackoutsJob(BaseJob):

    def _run(self):
        kaltura = Kaltura()
        for blackout in Blackout.all_blackouts():
            if blackout.end_date < utc_now():
                app.logger.info(f'Removing past blackout: {blackout}')
                Blackout.delete_blackout(blackout.id)
            else:
                end_date = localize_datetime(blackout.end_date)
                start_date = localize_datetime(blackout.start_date)
                events = kaltura.get_events_in_date_range(
                    end_date=end_date,
                    recurrence_type=KalturaScheduleEventRecurrenceType.RECURRENCE,
                    start_date=start_date,
                )
                for event in events:
                    created_by_diablo = CREATED_BY_DIABLO_TAG in event['tags']
                    if created_by_diablo and not represents_recording_series(event):
                        kaltura.delete(event['id'])
                        app.logger.info(f"'Event {event['summary']} deleted per {blackout}.")

    @classmethod
    def description(cls):
        return 'Deletes Course Capture (Kaltura) events according to the blackout dates set by Diablo admin.'

    @classmethod
    def key(cls):
        return 'blackouts'
