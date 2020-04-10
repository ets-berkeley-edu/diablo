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
from diablo.api.errors import ResourceNotFoundError
from diablo.api.util import admin_required
from diablo.jobs.admin_emails_job import AdminEmailsJob
from diablo.jobs.canvas_job import CanvasJob
from diablo.jobs.data_loch_sync_job import DataLochSyncJob
from diablo.jobs.dblink_to_redshift_job import DblinkToRedshiftJob
from diablo.jobs.kaltura_job import KalturaJob
from diablo.jobs.queued_emails_job import QueuedEmailsJob
from diablo.lib.http import tolerant_jsonify
from flask import current_app as app


@app.route('/api/job/<job_id>/start')
@admin_required
def start_job(job_id):
    job = next((job for job in _available_jobs() if job['id'] == job_id), None)
    if job:
        job['class'](app.app_context).run()
        return tolerant_jsonify({
            'id': job['id'],
            'description': job['description'],
        })
    else:
        raise ResourceNotFoundError(f'Invalid job_id: {job_id}')


@app.route('/api/jobs/available')
@admin_required
def available_jobs():
    jobs = []
    for job in _available_jobs():
        jobs.append({
            'id': job['id'],
            'description': job['description'],
        })
    return tolerant_jsonify(jobs)


def _available_jobs():
    return [
        {
            'id': 'admin_emails',
            'class': AdminEmailsJob,
            'description': 'Notify admins of relevant room and instructor changes.',
        },
        {
            'id': 'canvas',
            'class': CanvasJob,
            'description': 'Collect canvas-course-site IDs from Canvas and insert them into Diablo db.',
        },
        {
            'id': 'data_loch_sync',
            'class': DataLochSyncJob,
            'description': '[DEPRECATED] Get latest course, instructor and room data from the Data Lake.',
        },
        {
            'id': 'dblink_to_redshift',
            'class': DblinkToRedshiftJob,
            'description': 'Get latest course, instructor and room data from the Data Lake',
        },
        {
            'id': 'kaltura',
            'class': KalturaJob,
            'description': 'With Kaltura API, schedule recordings and link them to Canvas sites.',
        },
        {
            'id': 'queued_emails',
            'class': QueuedEmailsJob,
            'description': 'Send all email that is queued.',
        },
    ]
