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
import json
from os.path import dirname

from decorator import decorator
from diablo.lib.util import get_args_dict
from flask import current_app as app
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

__version__ = '1.2.4'

cache = Cache()

db = SQLAlchemy()

BASE_DIR = dirname(dirname(__file__))


def std_commit(allow_test_environment=False):
    """Commit failures in SQLAlchemy must be explicitly handled.

    This function follows the suggested default, which is to roll back and close the active session, letting the pooled
    connection start a new transaction cleanly. WARNING: Session closure will invalidate any in-memory DB entities. Rows
    will have to be reloaded from the DB to be read or updated.
    """
    # Give a hoot, don't pollute.
    if app.config['TESTING'] and not allow_test_environment:
        # When running tests, session flush generates id and timestamps that would otherwise show up during a commit.
        db.session.flush()
        return
    successful_commit = False
    try:
        db.session.commit()
        successful_commit = True
    except SQLAlchemyError:
        db.session.rollback()
        raise
    finally:
        if not successful_commit:
            db.session.close()


def cachify(key_pattern, timeout=1440):
    @decorator
    def _cachify(func, *args, **kw):
        args_dict = get_args_dict(func, *args, **kw)
        key = key_pattern.format(**args_dict)
        cached = cache.get(key)
        if cached is None:
            cached = func(*args, **kw)
            # timeout is in seconds
            cache.set(key, cached, timeout)
        return cached

    return _cachify


def skip_when_pytest(mock_object=None, is_fixture_json_file=False):
    @decorator
    def _skip_when_pytest(func, *args, **kw):
        if app.config['DIABLO_ENV'] == 'test':
            if mock_object and is_fixture_json_file:
                with open(f"{app.config['FIXTURES_PATH']}/{mock_object}", 'r') as file:
                    return json.loads(file.read())
            else:
                return mock_object
        else:
            return func(*args, **kw)
    return _skip_when_pytest
