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

from diablo import cachify
from flask import current_app as app
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Core import KalturaFilterPager, KalturaMediaEntryFilter
from KalturaClient.Plugins.Schedule import KalturaScheduleResourceFilter, KalturaSessionType


class Kaltura:

    client = None

    def __init__(self):
        if app.config['DIABLO_ENV'] == 'test':
            return

        admin_secret = app.config['KALTURA_ADMIN_SECRET']
        unique_user_id = app.config['KALTURA_UNIQUE_USER_ID']
        partner_id = app.config['KALTURA_PARTNER_ID']
        expiry = app.config['KALTURA_EXPIRY']

        config = KalturaConfiguration()
        self.client = KalturaClient(config)
        ks = self.client.session.start(
            admin_secret,
            unique_user_id,
            KalturaSessionType.ADMIN,
            partner_id,
            expiry,
            'appId:appName-appDomain',
        )
        self.client.setKs(ks)

    @cachify('kaltura/get_resource_list', timeout=120)
    def get_resource_list(self):
        response = self.client.schedule.scheduleResource.list(
            KalturaScheduleResourceFilter(),
            KalturaFilterPager(),
        )
        return [{'id': o.id, 'name': o.name} for o in response.objects]

    def ping(self):
        filter_ = KalturaMediaEntryFilter()
        filter_.nameLike = 'Love is the drug I\'m thinking of'
        result = self.client.media.list(filter_, KalturaFilterPager(pageSize=1))
        return result.totalCount is not None
