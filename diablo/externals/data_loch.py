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

from datetime import datetime

from flask import current_app as app
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Lazy init to support testing.
data_loch_db_rds = None


def sis_schema():
    return app.config['DATA_LOCH_SIS_SCHEMA']


def get_section_denormalized(term_id, section_id):
    sql = f"""
        SELECT * FROM {sis_schema()}.sis_sections
        WHERE sis_term_id = :term_id AND sis_section_id = :section_id
        ORDER BY sis_course_title, sis_section_id, instructor_uid
    """
    return safe_execute_rds(sql, term_id=term_id, section_id=section_id)


def get_sections_denormalized(term_id, instructor_uid):
    sql = f"""
        SELECT sis_section_id FROM {sis_schema()}.sis_sections
        WHERE sis_term_id = :term_id AND instructor_uid = :instructor_uid
    """
    section_ids = []
    for row in safe_execute_rds(sql, term_id=term_id, instructor_uid=instructor_uid):
        section_ids.append(row['sis_section_id'])
    sql = f"""
        SELECT * FROM {sis_schema()}.sis_sections
        WHERE sis_term_id = :term_id AND sis_section_id = ANY(:section_ids)
        ORDER BY sis_course_title, sis_section_id, instructor_uid
    """
    return safe_execute_rds(sql, term_id=term_id, section_ids=section_ids)


def safe_execute_rds(sql, **kwargs):
    global data_loch_db_rds
    if data_loch_db_rds is None:
        data_loch_db_rds = create_engine(app.config['DATA_LOCH_RDS_URI'])
    s = text(sql)
    try:
        ts = datetime.now().timestamp()
        dbresp = data_loch_db_rds.execute(s, **kwargs)
    except sqlalchemy.exc.SQLAlchemyError as err:
        app.logger.error(f'SQL {s} threw {err}')
        return None
    rows = dbresp.fetchall()
    query_time = datetime.now().timestamp() - ts
    row_array = [dict(r) for r in rows]
    app.logger.debug(f'Query returned {len(row_array)} rows in {query_time} seconds:\n{sql}\n{kwargs}')
    return row_array
