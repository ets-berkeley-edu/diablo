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
import os
import sys
import time

abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(abspath)

import click  # noqa
from diablo.factory import create_app  # noqa

application = create_app(standalone=True)


@application.cli.command('delete_scheduled_events_from_kaltura')
@click.argument('rehearsal', default=False)
def delete_kaltura_events(rehearsal):
    """Delete Kaltura events created by Diablo."""
    with application.app_context():
        from diablo.externals.kaltura import CREATED_BY_DIABLO_TAG, Kaltura

        def _print(message):
            print(f"""
                {'[REHEARSAL MODE]: ' if rehearsal else ''}{message}
            """)
        _print('Time for some Kaltura housekeeping...')
        kaltura = Kaltura()
        kaltura_events = kaltura.get_events_by_tag(tags_like=CREATED_BY_DIABLO_TAG)
        if kaltura_events:
            _print(f'In two seconds we will delete {len(kaltura_events)} event(s) in Kaltura. Use control-C to abort.')
            time.sleep(2)

            for event in kaltura_events:
                if not rehearsal:
                    kaltura.delete_event(kaltura_schedule_id=event['id'])
                _print(f'Deleted --> {event["description"] or event["summary"]}')
        else:
            _print(f'No events found with tag {CREATED_BY_DIABLO_TAG}')
        _print('Have a nice day!')


@application.cli.command('assign_kaltura_blackout_dates')
@click.argument('rehearsal', default=False)
def assign_blackout_dates(rehearsal):
    """Prevent other events from being scheduled in these dates."""
    with application.app_context():
        from diablo.externals.kaltura import Kaltura

        def _print(message):
            print(f"""
                {'[REHEARSAL MODE]: ' if rehearsal else ''}{message}
            """)
        blackout_dates = application.config['KALTURA_BLACKOUT_DATES']
        if blackout_dates:
            _print(f'Create blackout date(s) in Kaltura: {",".join(blackout_dates)}')
            _print('Use control-C to abort.')
            time.sleep(2)

            kaltura = Kaltura()
            for existing_blackout_date in kaltura.get_blackout_dates():
                for blackout_date in blackout_dates:
                    if blackout_date in existing_blackout_date['startDate']:
                        _print(f'[ERROR] Kaltura already has blackout_date {blackout_date}:\n{existing_blackout_date}')
                        _print('Either delete existing blackout dates in Kaltura or change Diablo configs.')
                        return

            if rehearsal:
                _print(f'kaltura.create_blackout_dates(blackout_dates=[{", ".join(blackout_dates)}])')
            else:
                kaltura_events = kaltura.create_blackout_dates(blackout_dates=blackout_dates)
                if kaltura_events:
                    _print('Blackout events created:')
                    for event in kaltura_events:
                        _print(event.summary)
        else:
            _print('Empty list of blackout_dates in Diablo config file.')

        _print('Have a nice day!')


@application.cli.command('delete_kaltura_event_by_id')
@click.argument('event_id')
def delete_kaltura_event(event_id):
    """Delete Kaltura event."""
    with application.app_context():
        from diablo.externals.kaltura import Kaltura

        Kaltura().delete_event(kaltura_schedule_id=event_id)
        print(f"""
            Kaltura event {event_id} deleted.
            Have a nice day.
        """)
