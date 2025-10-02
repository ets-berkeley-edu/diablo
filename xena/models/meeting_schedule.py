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

from datetime import date, datetime, timedelta

from flask import current_app as app

from xena.test_utils import util


class MeetingSchedule(object):

    def __init__(self, data):
        self.data = data

    @property
    def start_date(self):
        try:
            return self.data['start_date']
        except KeyError:
            date_str = app.config['CURRENT_TERM_BEGIN']
            return datetime.strptime(date_str, '%Y-%m-%d')

    @start_date.setter
    def start_date(self, value):
        self.data['start_date'] = value

    @property
    def record_start(self):
        term_start_str = app.config['CURRENT_TERM_BEGIN']
        term_record_start_str = app.config['CURRENT_TERM_RECORDINGS_BEGIN'] or term_start_str
        meeting_start_str = self.start_date.strftime('%Y-%m-%d')

        term_record_start_date = datetime.strptime(term_record_start_str, '%Y-%m-%d')
        meeting_start_date = datetime.strptime(meeting_start_str, '%Y-%m-%d')
        today = datetime.today()

        start_date = meeting_start_date if meeting_start_date > term_record_start_date else term_record_start_date
        return start_date if start_date > today else today

    @property
    def end_date(self):
        try:
            return self.data['end_date']
        except KeyError:
            date_str = app.config['CURRENT_TERM_END']
            return datetime.strptime(date_str, '%Y-%m-%d')

    @end_date.setter
    def end_date(self, value):
        self.data['end_date'] = value

    @property
    def record_end(self):
        date_str = self.end_date.strftime('%Y-%m-%d') or app.config['CURRENT_TERM_RECORDINGS_END']
        return datetime.strptime(date_str, '%Y-%m-%d')

    @property
    def days(self):
        return self.data['days']

    @days.setter
    def days(self, value):
        self.data['days'] = value

    @property
    def start_time(self):
        return self.data['start_time']

    @start_time.setter
    def start_time(self, value):
        self.data['start_time'] = value

    @property
    def end_time(self):
        return self.data['end_time']

    @end_time.setter
    def end_time(self, value):
        self.data['end_time'] = value

    @staticmethod
    def add_minutes(section_time_str, minutes):
        return datetime.strptime(section_time_str, '%I:%M %p') + timedelta(minutes=minutes)

    def get_berkeley_start_time(self):
        return self.add_minutes(self.start_time, 7)

    def get_berkeley_end_time(self):
        return self.add_minutes(self.end_time, 2)

    def __weekday_indices(self):
        weekdays = ['MO', 'TU', 'WE', 'TH', 'FR']
        weekday_indices = []
        for day in weekdays:
            if self.days and day in self.days:
                weekday_indices.append(weekdays.index(day))
        return weekday_indices

    @staticmethod
    def __holidays():
        holidays = []
        date_ranges = util.get_blackout_date_ranges()
        for date_range in date_ranges:
            for n in range(int((date_range[1] - date_range[0]).days) + 1):
                holidays.append(date_range[0] + timedelta(n))
        return holidays

    def expected_recording_dates(self, term):
        weekday_indices = self.__weekday_indices()
        holidays = self.__holidays()
        recording_dates = []
        if self.start_date and self.end_date:
            start = self.record_start.date()
            end = term.last_record_date.date() if self.end_date > term.last_record_date else self.end_date.date()
            delta = end - start

            for i in range(delta.days + 1):
                day = start + timedelta(i)
                if day.weekday() in weekday_indices and day not in holidays:
                    recording_dates.append(day)
        return recording_dates

    def expected_blackout_dates(self, term):
        weekday_indices = self.__weekday_indices()
        holidays = self.__holidays()

        today = date.today()
        start = self.start_date.date()
        end = term.last_record_date.date() if self.end_date > term.last_record_date else self.end_date.date()
        delta = end - start

        blackout_dates = []
        for i in range(delta.days + 1):
            day = start + timedelta(i)
            if day.weekday() in weekday_indices and day in holidays and day >= today:
                blackout_dates.append(day)
        return blackout_dates

    # Needed because Diablo can claim a series begins or ends on a blackout date
    def kaltura_series_days(self, term):
        start = self.record_start.date()
        end = term.last_record_date.date() if self.end_date > term.last_record_date else self.end_date.date()
        delta = end - start
        days = []
        for i in range(delta.days + 1):
            day = start + timedelta(i)
            if day.weekday() in self.__weekday_indices():
                days.append(day)
        return days

    def kaltura_series_start(self, term):
        days = self.kaltura_series_days(term)
        return days[0]

    def kaltura_series_end(self, term):
        days = self.kaltura_series_days(term)
        return days[-1]

    def date_with_no_recordings(self, term):
        # Return a blackout date within the recording series, or if none exists, return a Sunday.
        blackout_dates = self.__holidays()
        kaltura_series_start_date = self.kaltura_series_start(term)
        kaltura_series_end_date = self.kaltura_series_end(term)
        blackout_date_within_series = next((d for d in blackout_dates if d >= kaltura_series_start_date and d <= kaltura_series_end_date), None)
        if blackout_date_within_series:
            return blackout_date_within_series

        days_until_sunday = (6 - kaltura_series_start_date.weekday() + 7) % 7
        first_sunday_in_series = kaltura_series_start_date + timedelta(days=days_until_sunday)
        return first_sunday_in_series

    def date_range_for_ical_export(self, term):
        # Return 2 dates that are ~1 week apart where both dates are within the recording series
        # and, ideally, there is a blackout date between them.
        three_days = timedelta(days=3)
        six_days = timedelta(days=6)
        blackout_dates = self.__holidays()
        kaltura_series_start_date = self.kaltura_series_start(term)
        kaltura_series_end_date = self.kaltura_series_end(term)
        blackout_date_within_series = next((d for d in blackout_dates if d >= kaltura_series_start_date and d <= kaltura_series_end_date), None)
        if blackout_date_within_series:
            days_from_start = blackout_date_within_series - kaltura_series_start_date
            days_from_end = kaltura_series_end_date - blackout_date_within_series
            if days_from_start <= three_days:
                return blackout_date_within_series, blackout_date_within_series + six_days
            elif days_from_end <= three_days:
                return blackout_date_within_series - six_days, blackout_date_within_series
            else:
                return blackout_date_within_series - three_days, blackout_date_within_series + three_days
        return kaltura_series_start_date, kaltura_series_start_date + six_days
