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
from datetime import timedelta

import dateutil.parser
from flask import current_app as app
from xena.models.room import Room


class Meeting(object):

    def __init__(self, data):
        self.data = data

    @property
    def start_date(self):
        date_str = self.data['start_date'] or app.config['CURRENT_TERM_BEGIN']
        return datetime.strptime(date_str, '%Y-%m-%d')

    @property
    def end_date(self):
        date_str = self.data['end_date'] or app.config['CURRENT_TERM_END']
        return datetime.strptime(date_str, '%Y-%m-%d')

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

    @staticmethod
    def add_minutes(section_time_str, minutes):
        return datetime.strptime(section_time_str, '%I:%M %p') + timedelta(minutes=minutes)

    def get_berkeley_start_time(self):
        return Meeting.add_minutes(self.start_time, 7)

    def get_berkeley_end_time(self):
        return Meeting.add_minutes(self.end_time, 2)

    def expected_recording_dates(self, term):
        weekdays = ['MO', 'TU', 'WE', 'TH', 'FR']
        weekday_indices = []
        for day in weekdays:
            if day in self.days:
                weekday_indices.append(weekdays.index(day))

        start = self.start_date.date()
        end = term.last_record_date.date() if self.end_date > term.last_record_date else self.end_date.date()

        delta = end - start

        holidays = []
        for i in app.config['KALTURA_BLACKOUT_DATES']:
            day = dateutil.parser.parse(i).date()
            holidays.append(day)

        recording_dates = []
        for i in range(delta.days + 1):
            day = start + timedelta(i)
            if day.weekday() in weekday_indices and day not in holidays:
                recording_dates.append(day)

        return recording_dates
