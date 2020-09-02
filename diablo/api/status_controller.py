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
import traceback

from canvasapi.exceptions import CanvasException
from diablo import db
from diablo.externals.b_connected import BConnected
from diablo.externals.canvas import ping_canvas
from diablo.externals.kaltura import Kaltura
from diablo.externals.rds import log_db_error
from diablo.lib.http import tolerant_jsonify
from diablo.merged.emailer import send_system_error_email
from flask import current_app as app
import psycopg2
from sqlalchemy.exc import SQLAlchemyError


@app.route('/api/ping')
def ping():
    b_connected_ping = None
    canvas_ping = None
    db_ping = None
    kaltura_ping = None
    status = 200
    try:
        b_connected_ping = BConnected().ping()
        canvas_ping = _ping_canvas()
        db_ping = _db_status()
        kaltura_ping = Kaltura().ping()
    except Exception as e:
        status = 500
        subject = str(e)
        subject = f'{subject[:50]}...' if len(subject) > 50 else subject
        message = f'Error during /api/ping: {subject}'
        app.logger.error(message)
        app.logger.exception(e)
        if app.config['EMAIL_IF_PING_HAS_ERROR']:
            send_system_error_email(
                message=f'{message}\n\n<pre>{traceback.format_exc()}</pre>',
                subject=message,
            )
    finally:
        return tolerant_jsonify(
            {
                'app': True,
                'bConnected': b_connected_ping,
                'canvas': canvas_ping,
                'db': db_ping,
                'kaltura': kaltura_ping,
            },
            status=status,
        )


def _db_status():
    sql = 'SELECT 1'
    try:
        db.session.execute(sql)
        return True
    except psycopg2.Error as e:
        log_db_error(e, sql)
        return False
    except SQLAlchemyError as e:
        app.logger.error('Database connection error during /api/ping')
        app.logger.exception(e)
        return False


def _ping_canvas():
    try:
        return ping_canvas()
    except CanvasException as e:
        app.logger.error('Canvas error during /api/ping')
        app.logger.exception(e)
        return False
