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

abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(abspath)

from diablo.factory import create_app  # noqa

application = create_app(standalone=True)


@application.cli.command('delete_scheduled_events_from_kaltura')
def delete_scheduled_events_from_kaltura():
    """Delete Kaltura events created by Diablo."""
    with application.app_context():
        from diablo.models.scheduled import Scheduled
        from diablo.externals.kaltura import Kaltura

        print("""

            *** THIS IS A PROTOTYPE AND WILL NOT DELETE EVENTS IN KALTURA ***

        """)
        for scheduled in Scheduled.get_all_scheduled(application.config['CURRENT_TERM_ID']):
            kaltura_schedule_id = scheduled.kaltura_schedule_id
            print(f"""

                Delete Kaltura series {kaltura_schedule_id}, scheduled for course {scheduled.section_id}
                {Kaltura().get_schedule_event(kaltura_schedule_id=kaltura_schedule_id)}
            """)
