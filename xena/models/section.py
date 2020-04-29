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

from xena.models.room import Room
from xena.models.user import User


class Section(object):

    def __init__(self, data):
        self.data = data

    @property
    def term(self):
        return self.data['term']

    @property
    def ccn(self):
        return self.data['ccn']

    @property
    def code(self):
        return self.data['code']

    @property
    def number(self):
        return self.data['number']

    @property
    def title(self):
        return self.data['title']

    @property
    def instructors(self):
        return [User(i) for i in self.data['instructors']]

    @property
    def days(self):
        return self.data['days']

    @property
    def start_time(self):
        return self.data['start_time']

    @property
    def end_time(self):
        return self.data['end_time']

    @property
    def room(self):
        return Room(self.data['room'])

    @property
    def listings(self):
        return [Section(i) for i in self.data['listings']]
