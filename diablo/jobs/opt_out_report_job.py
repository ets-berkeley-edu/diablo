"""
Copyright ©2025. The Regents of the University of California (Regents). All Rights Reserved.

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
import tempfile

from flask import current_app as app

from diablo.externals import s3
from diablo.jobs.base_job import BaseJob
from diablo.jobs.util import get_eligible_courses
from diablo.lib.util import get_eb_environment


class OptOutReportJob(BaseJob):

    def _run(self):
        term_id = app.config['CURRENT_TERM_ID']

        tmpfile = tempfile.NamedTemporaryFile()
        with open(tmpfile.name, mode='wt', encoding='utf-8') as f:
            output = csv.DictWriter(f, fieldnames=['term_id', 'course_number', 'opted_out'])
            output.writeheader()
            for course in get_eligible_courses(term_id):
                output.writerow({
                    'term_id': term_id,
                    'course_number': course['sectionId'],
                    'opted_out': 'n' if course['hasOptedIn'] else 'y',
                })

        output_path = 'opt_out_report.csv'
        eb_env = get_eb_environment()
        if eb_env:
            output_path = f"{eb_env.replace('diablo-', '')}/{output_path}"

        with open(tmpfile.name, mode='rb') as f:
            s3.upload_binary_data(app.config['AWS_S3_OPT_OUT_REPORT_BUCKET'], output_path, f, 'text/csv')

    @classmethod
    def description(cls):
        return 'Generates a report on opt-out status of current-term eligible courses and uploads to S3.'

    @classmethod
    def key(cls):
        return 'opt_out_report'
