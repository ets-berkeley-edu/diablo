"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

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
import os

from diablo import cache
import diablo.factory
from flask_login import logout_user
from moto import mock_sts
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tests.util import override_config

os.environ['DIABLO_ENV'] = 'test'  # noqa


class FakeAuth(object):
    def __init__(self, the_app, the_client):
        self.app = the_app
        self.client = the_client

    def login(self, uid):
        with override_config(self.app, 'DEV_AUTH_ENABLED', True):
            params = {
                'uid': uid,
                'password': self.app.config['DEV_AUTH_PASSWORD'],
            }
            self.client.post(
                '/api/auth/dev_auth_login',
                data=json.dumps(params),
                content_type='application/json',
            )


# Because app and db fixtures are only created once per pytest run, individual tests
# are not able to modify application configuration values before the app is created.
# Per-test customizations could be supported via a fixture scope of 'function' and
# the @pytest.mark.parametrize annotation.

@pytest.fixture(scope='session')
def app(request):
    """Fixture application object, shared by all tests."""
    _app = diablo.factory.create_app()

    # Create app context before running tests.
    ctx = _app.app_context()
    ctx.push()

    # Pop the context after running tests.
    def teardown():
        cache.clear()
        ctx.pop()

    request.addfinalizer(teardown)

    return _app


# TODO Perform DB schema creation and deletion outside an app context, enabling test-specific app configurations.
@pytest.fixture(scope='session')
def db(app):
    """Fixture database object, shared by all tests."""
    from diablo.models import development_db
    # Drop all tables before re-loading the schemas.
    # If we dropped at teardown instead, an interrupted test run would block the next test run.
    development_db.clear()
    _db = development_db.load()

    return _db


@pytest.fixture(autouse=True, scope='function')
def logout():
    logout_user()


@pytest.fixture(scope='function', autouse=True)
def db_session(db):
    """Fixture database session used for the scope of a single test.

    All executions are wrapped in a session and then rolled back to keep individual tests isolated.
    """
    # Mixing SQL-using test fixtures with SQL-using decorators seems to cause timing issues with pytest's
    # fixture finalizers. Instead of using a finalizer to roll back the session and close connections,
    # we begin by cleaning up any previous invocations.
    # This fixture is marked 'autouse' to ensure that cleanup happens at the start of every test, whether
    # or not it has an explicit database dependency.
    db.session.rollback()
    try:
        bind = db.session.get_bind()
        if isinstance(bind, Engine):
            bind.dispose()
        else:
            bind.close()
    # The session bind will close only if it was provided a specific connection via this fixture.
    except TypeError:
        pass
    db.session.remove()

    connection = db.engine.connect()
    _session = scoped_session(sessionmaker(bind=connection))
    db.session = _session

    return _session


@pytest.fixture(scope='function')
def fake_auth(app, db, client):
    """Shortcut to start an authenticated session."""
    return FakeAuth(app, client)


@pytest.fixture(scope='session', autouse=True)
def fake_sts(app):
    """Fake the AWS security token service that Diablo relies on to deliver S3 content (photos, note attachments)."""
    mock_sts().start()
    yield
    mock_sts().stop()
