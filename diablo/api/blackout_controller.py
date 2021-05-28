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
from diablo.api.errors import BadRequestError, ResourceNotFoundError
from diablo.api.util import admin_required
from diablo.lib.http import tolerant_jsonify
from diablo.lib.util import localized_timestamp_to_utc
from diablo.models.blackout import Blackout
from flask import current_app as app, request


@app.route('/api/blackouts/all')
@admin_required
def get_all_blackouts():
    return tolerant_jsonify([blackout.to_api_json() for blackout in Blackout.all_blackouts()])


@app.route('/api/blackout/<blackout_id>')
@admin_required
def get_blackout(blackout_id):
    blackout = Blackout.get_blackout(blackout_id)
    if blackout:
        return tolerant_jsonify(blackout.to_api_json())
    else:
        raise ResourceNotFoundError('No such blackout')


@app.route('/api/blackout/<blackout_id>', methods=['DELETE'])
@admin_required
def delete_blackout(blackout_id):
    Blackout.delete_blackout(blackout_id)
    return tolerant_jsonify({'message': f'Email template {blackout_id} has been deleted'}), 200


@app.route('/api/blackout/create', methods=['POST'])
@admin_required
def create_blackout():
    params = request.get_json()
    name = params.get('name')
    start_date = params.get('startDate')
    end_date = params.get('endDate')
    if None in [name, start_date, end_date]:
        raise BadRequestError('Required parameters are missing.')

    start_date = _local_blackout_date_to_utc(f'{start_date}T00:00:00')
    end_date = _local_blackout_date_to_utc(f'{end_date}T23:59:59')
    _validate_date_range(start_date, end_date)

    blackout = Blackout.create(name=name, start_date=start_date, end_date=end_date)
    return tolerant_jsonify(blackout.to_api_json())


@app.route('/api/blackout/update', methods=['POST'])
@admin_required
def update_blackout():
    params = request.get_json()
    blackout_id = params.get('blackoutId')
    blackout = Blackout.get_blackout(blackout_id) if blackout_id else None
    if blackout:
        name = params.get('name')
        start_date = params.get('startDate')
        end_date = params.get('endDate')
        if None in [name, start_date, end_date]:
            raise BadRequestError('Required parameters are missing.')

        start_date = _local_blackout_date_to_utc(f'{start_date}T00:00:00')
        end_date = _local_blackout_date_to_utc(f'{end_date}T23:59:59')
        _validate_date_range(start_date, end_date)

        blackout = Blackout.update(
            blackout_id=blackout_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
        )
        return tolerant_jsonify(blackout.to_api_json())
    else:
        raise ResourceNotFoundError('No such email template')


def _validate_date_range(start_date, end_date, blackout_id=None):
    if start_date > end_date:
        raise BadRequestError('Start date must be less than or equal to end date.')

    for blackout in Blackout.all_blackouts():
        if blackout.id != blackout_id:
            latest_start = max(start_date, blackout.start_date)
            earliest_end = min(end_date, blackout.end_date)
            if max(0, (earliest_end - latest_start).days + 1) > 0:
                raise BadRequestError(f'Date range overlaps with existing blackout {blackout.id}')


def _local_blackout_date_to_utc(blackout_date):
    try:
        return localized_timestamp_to_utc(blackout_date)
    except ValueError:
        raise BadRequestError(f'{blackout_date} does not match expected date format.')
