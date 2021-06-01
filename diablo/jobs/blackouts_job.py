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
from datetime import date

from diablo.externals.kaltura import CREATED_BY_DIABLO_TAG, Kaltura
from diablo.jobs.base_job import BaseJob
from diablo.models.blackout import Blackout
from flask import current_app as app


class BlackoutsJob(BaseJob):

    def _run(self):
        today = date.today()
        kaltura = Kaltura()
        for blackout in Blackout.all_blackouts():
            if blackout.end_date.date() < today:
                app.logger.info(f'Removing past blackout: {blackout}')
                Blackout.delete_blackout(blackout.id)
            else:
                events = kaltura.get_events_in_date_range(end_date=blackout.end_date, start_date=blackout.start_date)
                for event in events:
                    if CREATED_BY_DIABLO_TAG in event['tags']:
                        kaltura.delete(event['id'])
                        app.logger.info(f"'Event {event['summary']} deleted per {blackout}.")

    @classmethod
    def description(cls):
        return 'Deletes Course Capture (Kaltura) events according to the blackout dates set by Diablo admin.'

    @classmethod
    def key(cls):
        return 'blackouts'
