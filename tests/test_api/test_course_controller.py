"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

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
import csv
from io import StringIO
import json

from diablo import std_commit
from diablo.jobs.emails_job import EmailsJob
from diablo.models.opt_out import OptOut
from diablo.models.scheduled import Scheduled
from diablo.models.sent_email import SentEmail
from diablo.models.sis_section import SisSection
from flask import current_app as app
from tests.test_api.api_test_utils import api_get_course, api_get_user, get_instructor_uids, mock_scheduled
from tests.util import override_config, simply_yield, test_scheduling_workflow

admin_uid = '90001'
collaborator_uid = '242881'
deleted_admin_user_uid = '910001'
deleted_section_id = 50018
section_1_id = 50000
section_2_id = 50001
section_3_id = 50002
section_4_id = 50004
section_5_id = 50003
section_6_id = 50005
section_7_id = 50010
section_8_id = 50017

section_in_ineligible_room = section_2_id
eligible_course_with_no_instructors = section_8_id


class TestGetCourse:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        """Deny access if user is not an admin."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_3_id,
            expected_status_code=403,
        )

    def test_deny_deleted_admin_user(self, client, fake_auth):
        """Deny access if admin user was deleted."""
        fake_auth.login(deleted_admin_user_uid)
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_invalid_section_id(self, client, fake_auth):
        """404 if section does not exist."""
        fake_auth.login(admin_uid)
        api_get_course(
            client,
            term_id=self.term_id,
            section_id=999999,
            expected_status_code=404,
        )

    def test_deleted_section(self, client, fake_auth):
        """404 if section does not exist."""
        fake_auth.login(admin_uid)
        assert SisSection.get_course(term_id=self.term_id, section_id=deleted_section_id, include_deleted=True)
        assert not SisSection.get_course(term_id=self.term_id, section_id=deleted_section_id)
        course = api_get_course(
            client,
            term_id=self.term_id,
            section_id=deleted_section_id,
        )
        assert course['deletedAt']

    def test_date_time_format(self, client, fake_auth):
        """Dates and times are properly formatted for front-end display."""
        instructor_uids = get_instructor_uids(section_id=section_2_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert api_json['meetings']['ineligible'][0]['daysFormatted'] == ['MO', 'WE', 'FR']
        assert api_json['meetings']['ineligible'][0]['startTimeFormatted'] == '3:00 pm'
        assert api_json['meetings']['ineligible'][0]['endTimeFormatted'] == '3:59 pm'
        assert api_json['meetings']['ineligible'][0]['location'] == 'Wheeler 150'
        assert api_json['nonstandardMeetingDates'] is False
        assert api_json['meetingType'] == 'A'

    def test_li_ka_shing_recording_options(self, client, fake_auth):
        """Rooms designated as 'auditorium' offer ALL types of recording."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_3_id,
        )
        assert api_json['meetings']['eligible'][0]['room']['location'] == 'Li Ka Shing 145'
        assert len(api_json['meetings']['eligible'][0]['room']['recordingTypeOptions']) == 2

    def test_no_administrative_proxy_for_course_page(self, client, fake_auth):
        """Course page screens out instructors with APRX role, but still returns a site."""
        fake_auth.login(uid=admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=50006,
        )
        assert api_json['sectionId'] == 50006
        assert api_json['instructors'] == []

    def test_cross_listing(self, client, fake_auth):
        """Course has cross-listings."""
        section_id = 50007
        cross_listed_section_ids = {50008, 50009}
        instructor_uid = '10008'
        fake_auth.login(uid=instructor_uid)

        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_id,
        )
        assert cross_listed_section_ids == set([c['sectionId'] for c in api_json['crossListings']])
        # Verify that cross-listed section_ids have been "deleted" in sis_sections table
        for section_id_ in cross_listed_section_ids:
            api_get_course(
                client,
                term_id=self.term_id,
                section_id=section_id_,
                expected_status_code=404,
            )

    def test_instructor_of_cross_listing(self, client, fake_auth):
        """If section X and Y are cross-listed then /course page of X must be reachable by instructor of Y."""
        section_id = 50012
        cross_listed_section_id = 50013
        instructor_uid = '10010'
        # Confirm that cross-listed section was deleted during sis_data_refresh job
        assert not SisSection.get_course(section_id=cross_listed_section_id, term_id=self.term_id)
        # Log in as instructor of cross-listed section
        fake_auth.login(uid=instructor_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_id,
        )
        assert len(api_json['crossListings']) == 1
        assert cross_listed_section_id == api_json['crossListings'][0]['sectionId']
        assert instructor_uid in [i['uid'] for i in api_json['instructors']]

    def test_no_cross_listing(self, client, fake_auth):
        """Course does not have cross-listing."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=section_2_id,
        )
        assert len(api_json['crossListings']) == 0

    def test_no_instructors(self, client, fake_auth):
        """Course with no instructors should be available."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=eligible_course_with_no_instructors,
        )
        assert len(api_json['instructors']) == 0

    def test_dual_mode_instruction(self, client, fake_auth):
        """Course is both online and in a physical location."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=50014,
        )
        eligible_meetings = api_json['meetings']['eligible']
        ineligible_meetings = api_json['meetings']['ineligible']
        assert len(eligible_meetings) == 1
        assert len(ineligible_meetings) == 2
        assert eligible_meetings[0]['location'] == 'Barker 101'
        assert ineligible_meetings[0]['location'] == 'Internet/Online'
        assert ineligible_meetings[1]['location'] == 'Dwinelle 155'
        assert ineligible_meetings[0]['startDate'] < ineligible_meetings[1]['startDate']
        assert api_json['nonstandardMeetingDates'] is True
        assert api_json['meetingType'] == 'C'

    def test_hybrid_instruction(self, client, fake_auth):
        """Course exists in two concurrent physical locations."""
        fake_auth.login(admin_uid)
        api_json = api_get_course(
            client,
            term_id=self.term_id,
            section_id=50015,
        )
        eligible_meetings = api_json['meetings']['eligible']
        ineligible_meetings = api_json['meetings']['ineligible']
        assert len(eligible_meetings) == 1
        assert len(ineligible_meetings) == 1
        assert eligible_meetings[0]['startDate'] == ineligible_meetings[0]['startDate']
        assert api_json['nonstandardMeetingDates'] is False
        assert eligible_meetings[0]['location'] == 'Barker 101'
        assert eligible_meetings[0]['eligible'] is True
        assert ineligible_meetings[0]['location'] == 'LeConte 1'
        assert ineligible_meetings[0]['eligible'] is False
        assert api_json['meetingType'] == 'B'

    def test_meeting_recording_end_date(self, client, fake_auth):
        # The term ends on a Tuesday
        fake_auth.login(admin_uid)
        with override_config(app, 'CURRENT_TERM_END', '2020-11-24'):
            api_json = api_get_course(
                client,
                term_id=self.term_id,
                section_id=50015,
            )
            assert api_json['meetings']['eligible'][0]['endDate'] == '2021-12-11'
            # The course meets on ['MO', 'WE', 'FR']. The last recordings is on Wed preceding term_end
            assert api_json['meetings']['eligible'][0]['recordingEndDate'] == '2021-11-24'
            assert api_json['meetings']['ineligible'][0]['endDate'] == '2021-12-11'
            assert 'recordingEndDate' not in api_json['meetings']['ineligible'][0]


class TestGetCourseSite:

    @staticmethod
    def _api_course_site(client, site_id, expected_status_code=200):
        response = client.get(f'/api/course_site/{site_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_course_site(client, site_id='1234567', expected_status_code=401)

    def test_not_admin(self, client, fake_auth):
        """Deny non-admin access."""
        fake_auth.login(collaborator_uid)
        self._api_course_site(client, site_id='1234567', expected_status_code=401)

    def test_admin(self, client, fake_auth):
        """Admin can view site properties."""
        fake_auth.login(admin_uid)
        response = self._api_course_site(client, site_id='1234567')
        assert response['canvasSiteId'] == '1234567'


class TestGetCourses:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_courses(client, term_id, filter_=None, expected_status_code=200):
        response = client.post(
            '/api/courses',
            data=json.dumps({
                'termId': term_id,
                'filter': filter_ or 'Scheduled',
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_courses(client, term_id=self.term_id, expected_status_code=401)

    def test_opted_out_filter(self, client, fake_auth):
        """Opted Out filter: Courses in eligible room; "opt out" is true; not scheduled."""
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            # Send invites them opt_out.
            for section_id in (section_1_id, section_in_ineligible_room, section_3_id, section_4_id):
                instructor_uids = get_instructor_uids(section_id=section_id, term_id=self.term_id)
                OptOut.update_opt_out(instructor_uid=instructor_uids[0], section_id=section_id, term_id=self.term_id, opt_out=True)

                in_enabled_room = _is_course_in_enabled_room(section_id=section_id, term_id=self.term_id)
                if section_id == section_in_ineligible_room:
                    # Courses in ineligible rooms will be excluded from the feed.
                    assert not in_enabled_room
                else:
                    assert in_enabled_room

            api_json = self._api_courses(client, term_id=self.term_id, filter_='Opted Out')

            # Opted-out courses are in the feed, whether scheduled or not
            assert _find_course(api_json=api_json, section_id=section_1_id, term_id=self.term_id)
            assert _find_course(api_json=api_json, section_id=section_3_id, term_id=self.term_id)
            assert _find_course(api_json=api_json, section_id=section_4_id, term_id=self.term_id)
            # Ineligible courses are not in the feed
            assert not _find_course(api_json=api_json, section_id=section_in_ineligible_room, term_id=self.term_id)

    def test_scheduled_filter(self, client, fake_auth):
        """Scheduled filter: Courses with recordings scheduled."""
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            # Feed will only include courses that were scheduled.
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            mock_scheduled(
                section_id=deleted_section_id,
                term_id=self.term_id,
            )
            # Ignore if 'scheduled' record is deleted.
            mock_scheduled(
                section_id=section_2_id,
                term_id=self.term_id,
            )
            Scheduled.delete(section_id=section_2_id, term_id=self.term_id)
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Scheduled')
            assert len(api_json) == 2
            assert _find_course(api_json=api_json, section_id=section_1_id, term_id=self.term_id)
            assert not _find_course(api_json=api_json, section_id=section_6_id, term_id=self.term_id)

    def test_no_instructors_filter(self, client, fake_auth):
        """Eligible courses without instructors attached."""
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            # Course with instructor.
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            # Course without instructor.
            mock_scheduled(
                section_id=section_8_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            api_json = self._api_courses(client, term_id=self.term_id, filter_='No Instructors')
            assert len(api_json) == 1
            assert api_json[0]['sectionId'] == section_8_id
            assert api_json[0]['instructors'] == []

    def test_eligible_filter(self, client, fake_auth):
        """The 'eligible' filter returns all courses in eligible rooms."""
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            # Put courses in a few different states.
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            # We gotta catch 'em all.
            api_json = self._api_courses(client, term_id=self.term_id, filter_='Eligible')
            assert len(api_json) == 11
            for section_id in [section_1_id, section_3_id, section_4_id, section_5_id, section_6_id]:
                assert _find_course(api_json=api_json, section_id=section_id, term_id=self.term_id)
            assert not _find_course(api_json=api_json, section_id=section_in_ineligible_room, term_id=self.term_id)

    def test_all_filter(self, client, fake_auth):
        """The 'all' filter returns even ineligible courses."""
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            # Put courses in a few different states.
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            std_commit(allow_test_environment=True)
            # We gotta catch 'em all.
            api_json = self._api_courses(client, term_id=self.term_id, filter_='All')
            assert len(api_json) == 15
            for section_id in [section_1_id, section_3_id, section_4_id, section_5_id, section_6_id]:
                assert _find_course(api_json=api_json, section_id=section_id, term_id=self.term_id)
            assert _find_course(api_json=api_json, section_id=section_in_ineligible_room, term_id=self.term_id)


class TestDownloadCoursesCsv:

    @staticmethod
    def _api_courses_csv(client, expected_status_code=200):
        response = client.post(
            '/api/courses/csv',
            data=json.dumps({
                'termId': app.config['CURRENT_TERM_ID'],
                'filter': 'All',
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.data

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses_csv(client, expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        """Deny access if user is not an admin."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=app.config['CURRENT_TERM_ID'])
        fake_auth.login(instructor_uids[0])
        self._api_courses_csv(client, expected_status_code=401)

    def test_download_csv(self, client, fake_auth):
        """Admin users can download courses CSV file."""
        fake_auth.login(admin_uid)
        term_id = app.config['CURRENT_TERM_ID']
        csv_string = self._api_courses_csv(client).decode('utf-8')
        reader = csv.reader(StringIO(csv_string), delimiter=',')
        for index, row in enumerate(reader):
            section_id = row[1]
            meeting_type = row[6]
            sign_up_url = row[9]
            instructors = row[-3]
            instructor_uids = row[-2]
            if index == 0:
                assert section_id == 'Section Id'
                assert meeting_type == 'Meeting Type'
                assert sign_up_url == 'Sign-up URL'
                assert instructors == 'Instructors'
                assert instructor_uids == 'Instructor UIDs'
            else:
                course = SisSection.get_course(section_id=section_id, term_id=term_id)
                assert int(section_id) == course['sectionId']
                for snippet in [app.config['DIABLO_BASE_URL'], section_id, str(term_id)]:
                    assert snippet in sign_up_url

                expected_uids = [instructor['uid'] for instructor in course['instructors']]
                if expected_uids:
                    assert set(instructor_uids.split(', ')) == set(expected_uids)
                else:
                    assert instructor_uids == ''
                for instructor in course['instructors']:
                    assert instructor['email'] in instructors
                    assert instructor['name'] in instructors

                if len(course['meetings']['eligible']) > 1:
                    assert meeting_type == 'D'
                elif course['nonstandardMeetingDates']:
                    assert meeting_type == 'C'
                elif len(course['meetings']['eligible'] + course['meetings']['ineligible']) > 1:
                    assert meeting_type == 'B'
                else:
                    assert meeting_type == 'A'


class TestCrossListedNameGeneration:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    def test_different_course_names(self, client, fake_auth):
        """Departments sharing catalog id and section code."""
        fake_auth.login(admin_uid)
        self._verify_name_generation(
            client=client,
            section_id=section_7_id,
            expected_name='MATH C51, LEC 001 | STAT C51, LEC 003',
        )

    def test_different_instruction_format(self, client, fake_auth):
        """Departments share catalog id but not section code."""
        fake_auth.login(admin_uid)
        self._verify_name_generation(
            client=client,
            section_id=50012,
            expected_name='MATH C51, LEC 001 | STAT C151, COL 001',
        )

    def _verify_name_generation(self, client, section_id, expected_name):
        # section_id = self._create_cross_listed(courses=courses)
        api_json = api_get_course(
            client,
            section_id=section_id,
            term_id=self.term_id,
        )
        assert api_json['label'] == expected_name, f'Failed on section_id={section_id}'

        cross_listings = api_json['crossListings']
        assert len(cross_listings) >= 1
        api_get_course(
            client,
            section_id=cross_listings[0]['sectionId'],
            term_id=self.term_id,
            expected_status_code=404,
        )


class TestUpdateCollaboratorUids:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_collaborator_uids_update(
            client,
            term_id,
            section_id,
            collaborator_uids,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/collaborator_uids/update',
            data=json.dumps({
                'collaboratorUids': collaborator_uids,
                'sectionId': section_id,
                'termId': term_id,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_collaborator_uids_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            collaborator_uids=[collaborator_uid],
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        fake_auth.login(collaborator_uid)
        self._api_collaborator_uids_update(
            client,
            collaborator_uids=[collaborator_uid],
            section_id=section_1_id,
            term_id=self.term_id,
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Update the 'collaborator_uids' course preference."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        self._api_collaborator_uids_update(
            client,
            collaborator_uids=[collaborator_uid],
            section_id=section_1_id,
            term_id=self.term_id,
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['collaboratorUids'] == [collaborator_uid]


class TestUpdatePublishType:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_publish_type_update(
            client,
            term_id,
            section_id,
            publish_type,
            canvas_site_ids=None,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/publish_type/update',
            data=json.dumps({
                'canvasSiteIds': canvas_site_ids,
                'publishType': publish_type,
                'sectionId': section_id,
                'termId': term_id,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        fake_auth.login(collaborator_uid)
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            expected_status_code=401,
        )

    def test_canvas_site_ids_required(self, client, fake_auth):
        # kaltura_media_gallery setting requires Canvas site IDs.
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['publishType'] == 'kaltura_my_media'
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            expected_status_code=400,
        )

    def test_publish_authorized(self, client, fake_auth):
        """Update the 'publish_type' course preference."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['publishType'] == 'kaltura_my_media'
        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            canvas_site_ids=[1234567],
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['publishType'] == 'kaltura_media_gallery'
        assert course['canvasSiteIds'] == [1234567]

        self._api_publish_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            publish_type='kaltura_media_gallery',
            canvas_site_ids=[1234567, 1234568],
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['publishType'] == 'kaltura_media_gallery'
        assert course['canvasSiteIds'] == [1234567, 1234568]

        publish_type_updates = [u for u in course['updateHistory'] if u['fieldName'] == 'publish_type']
        assert len(publish_type_updates) == 1
        assert publish_type_updates[0]['fieldValueOld'] == 'kaltura_my_media'
        assert publish_type_updates[0]['fieldValueNew'] == 'kaltura_media_gallery'
        assert publish_type_updates[0]['status'] == 'queued'
        assert publish_type_updates[0]['requestedByUid'] == instructor_uids[0]
        assert publish_type_updates[0]['requestedByName'] == 'William Peter Blatty'

        canvas_site_updates = [u for u in course['updateHistory'] if u['fieldName'] == 'canvas_site_ids']
        assert len(canvas_site_updates) == 2
        assert canvas_site_updates[1]['fieldValueOld'] is None
        assert canvas_site_updates[1]['fieldValueNew'] == ['1234567']
        assert canvas_site_updates[1]['status'] == 'queued'
        assert canvas_site_updates[1]['requestedByUid'] == instructor_uids[0]
        assert canvas_site_updates[1]['requestedByName'] == 'William Peter Blatty'
        assert canvas_site_updates[0]['fieldValueOld'] == ['1234567']
        assert canvas_site_updates[0]['fieldValueNew'] == ['1234567', '1234568']
        assert canvas_site_updates[0]['status'] == 'queued'
        assert canvas_site_updates[0]['requestedByUid'] == instructor_uids[0]
        assert canvas_site_updates[0]['requestedByName'] == 'William Peter Blatty'


class TestUpdateRecordingType:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_recording_type_update(
            client,
            term_id,
            section_id,
            recording_type,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/recording_type/update',
            data=json.dumps({
                'termId': term_id,
                'sectionId': section_id,
                'recordingType': recording_type,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_recording_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            recording_type='presenter_presentation_audio_with_operator',
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        fake_auth.login(collaborator_uid)
        self._api_recording_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            recording_type='presenter_presentation_audio_with_operator',
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Update the 'recording_type' course preference."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['recordingType'] == 'presenter_presentation_audio'
        self._api_recording_type_update(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            recording_type='presenter_presentation_audio_with_operator',
        )
        std_commit(allow_test_environment=True)

        course = SisSection.get_course(section_id=section_1_id, term_id=self.term_id)
        assert course['recordingType'] == 'presenter_presentation_audio_with_operator'

        recording_type_updates = [u for u in course['updateHistory'] if u['fieldName'] == 'recording_type']
        assert len(recording_type_updates) == 1
        assert recording_type_updates[0]['fieldValueOld'] == 'presenter_presentation_audio'
        assert recording_type_updates[0]['fieldValueNew'] == 'presenter_presentation_audio_with_operator'
        assert recording_type_updates[0]['status'] == 'queued'
        assert recording_type_updates[0]['requestedByUid'] == instructor_uids[0]
        assert recording_type_updates[0]['requestedByName'] == 'William Peter Blatty'

        def _get_operator_emails():
            return SentEmail.get_emails_of_type(
                section_ids=[section_1_id],
                template_type='admin_operator_requested',
                term_id=self.term_id,
            )
        assert len(_get_operator_emails()) == 0
        EmailsJob(simply_yield).run()
        assert len(_get_operator_emails()) == 1


class TestUpdateOptOut:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_opt_out_update(
            client,
            instructor_uid,
            term_id,
            section_id,
            opt_out,
            expected_status_code=200,
    ):
        response = client.post(
            '/api/course/opt_out/update',
            data=json.dumps({
                'instructorUid': instructor_uid,
                'termId': term_id,
                'sectionId': section_id,
                'optOut': opt_out,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        self._api_opt_out_update(
            client,
            instructor_uid=instructor_uids[0],
            term_id=self.term_id,
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Deny non-instructors."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login([collaborator_uid])
        self._api_opt_out_update(
            client,
            instructor_uid=instructor_uids[0],
            term_id=self.term_id,
            section_id=section_1_id,
            opt_out=True,
            expected_status_code=401,
        )

    def test_authorized(self, client, fake_auth):
        """Instructors can toggle the opt-out preference for courses."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        with test_scheduling_workflow(app):
            opt_outs = OptOut.get_opt_outs_for_section(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            assert not len(opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is False

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            opt_outs = OptOut.get_opt_outs_for_section(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            assert len(opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is True
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is True

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            opt_outs = OptOut.get_opt_outs_for_section(
                section_id=section_1_id,
                term_id=self.term_id,
            )
            assert not len(opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is False

            opt_out_updates = [u for u in course_feed['updateHistory'] if u['fieldName'] == 'opted_out']
            assert len(opt_out_updates) == 2
            assert opt_out_updates[1]['fieldValueOld'] is None
            assert opt_out_updates[1]['fieldValueNew'] == instructor_uids[0]
            assert opt_out_updates[1]['status'] == 'queued'
            assert opt_out_updates[1]['requestedByUid'] == instructor_uids[0]
            assert opt_out_updates[1]['requestedByName'] == 'William Peter Blatty'
            assert opt_out_updates[0]['fieldValueOld'] == instructor_uids[0]
            assert opt_out_updates[0]['fieldValueNew'] is None
            assert opt_out_updates[0]['status'] == 'queued'
            assert opt_out_updates[0]['requestedByUid'] == instructor_uids[0]
            assert opt_out_updates[0]['requestedByName'] == 'William Peter Blatty'

    def test_authorized_blanket_per_term(self, client, fake_auth):
        """Instructors can toggle the opt-out preference for all courses in a term."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        with test_scheduling_workflow(app):
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )

            blanket_term_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=self.term_id,
            )
            assert not len(blanket_term_opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is False

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id='all',
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            blanket_term_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=self.term_id,
            )
            assert len(blanket_term_opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is True
            assert course_feed['hasOptedOut'] is True
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is True

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id='all',
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            blanket_term_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=self.term_id,
            )
            assert not len(blanket_term_opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is False

            # Blanket opt-outs still leave notations in per-course update history.
            opt_out_updates = [u for u in course_feed['updateHistory'] if u['fieldName'] == 'opted_out']
            assert len(opt_out_updates) == 2
            assert opt_out_updates[1]['fieldValueOld'] is None
            assert opt_out_updates[1]['fieldValueNew'] == instructor_uids[0]
            assert opt_out_updates[1]['status'] == 'queued'
            assert opt_out_updates[1]['requestedByUid'] == instructor_uids[0]
            assert opt_out_updates[1]['requestedByName'] == 'William Peter Blatty'
            assert opt_out_updates[0]['fieldValueOld'] == instructor_uids[0]
            assert opt_out_updates[0]['fieldValueNew'] is None
            assert opt_out_updates[0]['status'] == 'queued'
            assert opt_out_updates[0]['requestedByUid'] == instructor_uids[0]
            assert opt_out_updates[0]['requestedByName'] == 'William Peter Blatty'

    def test_authorized_blanket_all_terms(self, client, fake_auth):
        """Instructors can toggle the opt-out preference for all courses in all terms."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        with test_scheduling_workflow(app):
            mock_scheduled(
                section_id=section_1_id,
                term_id=self.term_id,
            )

            blanket_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=None,
            )
            assert not len(blanket_opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is False

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id='all',
                section_id='all',
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            blanket_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=None,
            )
            assert len(blanket_opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is True
            assert course_feed['hasOptedOut'] is True
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is True

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id='all',
                section_id='all',
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            blanket_opt_outs = OptOut.get_opt_outs_for_section(
                section_id=None,
                term_id=None,
            )
            assert not len(blanket_opt_outs)
            course_feed = api_get_course(client, self.term_id, section_1_id)
            assert course_feed['hasBlanketOptedOut'] is False
            assert course_feed['hasOptedOut'] is False
            assert next(i['hasOptedOut'] for i in course_feed['instructors'] if i['uid'] == instructor_uids[0]) is False

            # Blanket opt-outs still leave notations in per-course update history.
            opt_out_updates = [u for u in course_feed['updateHistory'] if u['fieldName'] == 'opted_out']
            assert len(opt_out_updates) == 2
            assert opt_out_updates[1]['fieldValueOld'] is None
            assert opt_out_updates[1]['fieldValueNew'] == instructor_uids[0]
            assert opt_out_updates[1]['status'] == 'queued'
            assert opt_out_updates[1]['requestedByUid'] == instructor_uids[0]
            assert opt_out_updates[1]['requestedByName'] == 'William Peter Blatty'
            assert opt_out_updates[0]['fieldValueOld'] == instructor_uids[0]
            assert opt_out_updates[0]['fieldValueNew'] is None
            assert opt_out_updates[0]['status'] == 'queued'
            assert opt_out_updates[0]['requestedByUid'] == instructor_uids[0]
            assert opt_out_updates[0]['requestedByName'] == 'William Peter Blatty'

    def test_admin_toggle_opt_out(self, client, fake_auth):
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=True,
            )
            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['hasOptedOut'] is True

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id=section_1_id,
                opt_out=False,
            )
            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['hasOptedOut'] is False

    def test_admin_toggle_blanket_opt_out(self, client, fake_auth):
        fake_auth.login(admin_uid)
        with test_scheduling_workflow(app):
            instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id='all',
                opt_out=True,
            )
            std_commit(allow_test_environment=True)

            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['hasOptedOut'] is True
            api_json = api_get_user(client, uid=instructor_uids[0])
            assert api_json['hasOptedOutForTerm'] is True

            self._api_opt_out_update(
                client,
                instructor_uid=instructor_uids[0],
                term_id=self.term_id,
                section_id='all',
                opt_out=False,
            )
            std_commit(allow_test_environment=True)

            api_json = api_get_course(client, section_id=section_1_id, term_id=self.term_id)
            assert api_json['hasOptedOut'] is False
            api_json = api_get_user(client, uid=instructor_uids[0])
            assert api_json['hasOptedOutForTerm'] is False


class TestNote:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_update_note(client, term_id, section_id, body, expected_status_code=200):
        response = client.post(
            '/api/course/note/update',
            data=json.dumps({
                'termId': term_id,
                'sectionId': section_id,
                'body': body,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    @staticmethod
    def _api_delete_note(client, term_id, section_id, expected_status_code=200):
        response = client.post(
            '/api/course/note/delete',
            data=json.dumps({
                'termId': term_id,
                'sectionId': section_id,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_anonymous(self, client):
        """Denies anonymous access."""
        self._api_update_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            body='Nota bene',
            expected_status_code=401,
        )
        self._api_delete_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_unauthorized(self, client, fake_auth):
        """Denies non-admin access."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_update_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            body='Nota bene',
            expected_status_code=401,
        )
        self._api_delete_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            expected_status_code=401,
        )

    def test_no_body(self, client, fake_auth):
        """Updates require note body."""
        fake_auth.login(admin_uid)
        self._api_update_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            body=None,
            expected_status_code=400,
        )

    def test_nonexistent_section(self, client, fake_auth):
        """Updates require matching section."""
        fake_auth.login(admin_uid)
        self._api_update_note(
            client,
            term_id=self.term_id,
            section_id='0',
            body='Nota bene',
            expected_status_code=400,
        )

    def test_admin(self, client, fake_auth):
        """Admin can create, update and delete note."""
        fake_auth.login(admin_uid)
        assert 'note' not in client.get(f'/api/course/{self.term_id}/{section_1_id}').json

        response = self._api_update_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            body='Nota bene',
        )
        assert response['note'] == 'Nota bene'
        assert client.get(f'/api/course/{self.term_id}/{section_1_id}').json['note'] == 'Nota bene'

        # Notes are not visible to non-admins.
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        assert 'note' not in client.get(f'/api/course/{self.term_id}/{section_1_id}').json

        fake_auth.login(admin_uid)
        response = self._api_update_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
            body='Nota male',
        )
        assert response['note'] == 'Nota male'
        assert client.get(f'/api/course/{self.term_id}/{section_1_id}').json['note'] == 'Nota male'

        response = self._api_delete_note(
            client,
            term_id=self.term_id,
            section_id=section_1_id,
        )
        assert response == {'deleted': True}
        assert 'note' not in client.get(f'/api/course/{self.term_id}/{section_1_id}').json


class TestCoursesReport:

    @property
    def term_id(self):
        return app.config['CURRENT_TERM_ID']

    @staticmethod
    def _api_courses_report(client, term_id, expected_status_code=200):
        response = client.get(f'/api/courses/report/{term_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Deny anonymous access."""
        self._api_courses_report(client, term_id=self.term_id, expected_status_code=401)

    def test_unauthorized(self, client, fake_auth):
        """Instructors cannot view courses report."""
        instructor_uids = get_instructor_uids(section_id=section_1_id, term_id=self.term_id)
        fake_auth.login(instructor_uids[0])
        self._api_courses_report(client, term_id=self.term_id, expected_status_code=401)

    def test_total_scheduled_count(self, client, fake_auth):
        """The courses report includes valid total_scheduled_count."""
        fake_auth.login(admin_uid)
        report = self._api_courses_report(client, term_id=self.term_id)
        assert report['totalScheduledCount'] == len(Scheduled.get_all_scheduled(self.term_id))


def _find_course(api_json, section_id, term_id):
    return next((s for s in api_json if s['sectionId'] == section_id and s['termId'] == term_id), None)


def _is_course_in_enabled_room(section_id, term_id):
    eligible_meetings = SisSection.get_course(term_id=term_id, section_id=section_id)['meetings']['eligible']
    return eligible_meetings and eligible_meetings[0]['room']['capability'] is not None
