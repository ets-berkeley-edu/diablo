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
import csv

from diablo.jobs.util import register_cross_listings


class TestIdentifyCrossListings:

    def test_register_cross_listings(self, app):
        """Uses SIS data export to identify cross-listed sections."""
        rows = []
        with open(f"{app.config['FIXTURES_PATH']}/sis/class_schedule_by_section_id.csv", 'r') as csv_file:
            for row in csv.DictReader(csv_file):
                rows.append({
                    'section_id': int(row['section_id']),
                    'schedule': row['schedule'],
                })
            cross_listings = register_cross_listings(rows, app.config['CURRENT_TERM_ID'])
            assert len(cross_listings) == 677
            assert cross_listings[32712] == [32713, 32943, 32945]
            for non_cross_listed in [28135, 31049]:
                assert non_cross_listed not in cross_listings
