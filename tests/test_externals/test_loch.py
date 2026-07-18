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
from unittest.mock import MagicMock, patch

from sqlalchemy.sql import text

from diablo import db
from diablo.externals import loch
from diablo.lib.util import basic_attributes_to_api_json


class TestGetLochBasicAttributes:
    """Regression coverage for SQLAlchemy 2.0's removal of string-key indexing on Row objects.

    Under SQLAlchemy 1.x, ``Row`` supported ``row['some_column']``. Under 2.0, ``Row`` behaves like a
    plain tuple and raises ``TypeError: tuple indices must be integers or slices, not str`` on string
    access; callers must go through ``row._mapping`` instead. Because DIABLO_ENV=='test' always short-
    circuits to JSON fixtures (which are plain dicts), this regression was invisible to the existing
    suite. These tests force the real query branch, using genuine SQLAlchemy Row objects (fetched via a
    literal SELECT against the test database, bypassing dblink) as the mocked execution result.
    """

    @staticmethod
    def _real_rows():
        return db.session.execute(
            text("""
                SELECT 'uid1' AS uid, 'csid1' AS csid, 'First' AS first_name, 'Last' AS last_name,
                       'first.last@berkeley.edu' AS email
            """),
        ).all()

    def test_get_loch_basic_attributes_returns_subscriptable_dicts(self, app, monkeypatch):
        monkeypatch.setenv('DIABLO_ENV', 'production')
        mock_session = MagicMock()
        mock_session.return_value.execute.return_value.all.return_value = self._real_rows()

        with patch('diablo.externals.loch.db.session', mock_session):
            results = loch.get_loch_basic_attributes(['uid1'])

        assert results == [{
            'uid': 'uid1',
            'csid': 'csid1',
            'first_name': 'First',
            'last_name': 'Last',
            'email': 'first.last@berkeley.edu',
        }]
        assert basic_attributes_to_api_json(results[0]) == {
            'csid': 'csid1',
            'email': 'first.last@berkeley.edu',
            'firstName': 'First',
            'lastName': 'Last',
            'uid': 'uid1',
        }

    def test_get_loch_basic_attributes_by_uid_or_email_returns_subscriptable_dicts(self, app, monkeypatch):
        monkeypatch.setenv('DIABLO_ENV', 'production')
        mock_session = MagicMock()
        mock_session.return_value.execute.return_value.all.return_value = self._real_rows()

        with patch('diablo.externals.loch.db.session', mock_session):
            results = loch.get_loch_basic_attributes_by_uid_or_email('uid1')

        assert results == [{
            'uid': 'uid1',
            'csid': 'csid1',
            'first_name': 'First',
            'last_name': 'Last',
            'email': 'first.last@berkeley.edu',
        }]
        assert basic_attributes_to_api_json(results[0])['uid'] == 'uid1'
