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

from diablo import cachify, skip_when_pytest
from diablo.lib.berkeley import term_name_for_sis_id
from diablo.lib.kaltura_util import events_to_api_json, get_first_matching_datetime_of_term
from diablo.lib.util import to_isoformat
from flask import current_app as app
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Core import KalturaCategoryFilter, KalturaFilterPager, KalturaMediaEntryFilter
from KalturaClient.Plugins.Schedule import KalturaRecordScheduleEvent, KalturaScheduleEventClassificationType, \
    KalturaScheduleEventFilter, KalturaScheduleEventRecurrence, KalturaScheduleEventRecurrenceFrequency, \
    KalturaScheduleEventRecurrenceType, KalturaScheduleEventResource, KalturaScheduleEventStatus, \
    KalturaScheduleResourceFilter, KalturaSessionType

# Avoid infinite loop when paging through Kaltura results
MAX_PAGE = 100


class Kaltura:

    def __init__(self):
        self.kaltura_partner_id = app.config['KALTURA_PARTNER_ID']
        if app.config['DIABLO_ENV'] == 'test':
            return

    @skip_when_pytest()
    def delete_scheduled_recordings(self, kaltura_schedule_id):
        return self.kaltura_client.schedule.scheduleEvent.delete(kaltura_schedule_id)

    @cachify('kaltura/get_schedule_event_list', timeout=30)
    def get_schedule_event_list(self, kaltura_resource_id):
        objects = []
        page_index, page_size = 1, 200
        while page_index < MAX_PAGE:
            response = self.kaltura_client.schedule.scheduleEvent.list(
                filter=KalturaScheduleEventFilter(resourceIdsLike=str(kaltura_resource_id)),
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=page_size),
            )
            objects += response.objects
            if len(response.objects) < page_size:
                break
            page_size += 1

        return events_to_api_json(objects)

    @cachify('kaltura/kaltura_schedule_event')
    def get_schedule_event(self, kaltura_schedule_id):
        event = self.kaltura_client.schedule.scheduleEvent.get(scheduleEventId=kaltura_schedule_id)
        return None if event is None else {
            'id': event.id,
            'description': event.description,
        }

    @cachify('kaltura/get_resource_list', timeout=30)
    def get_resource_list(self):
        objects = []
        page_index, page_size = 1, 200
        while page_index < MAX_PAGE:
            response = self.kaltura_client.schedule.scheduleResource.list(
                filter=KalturaScheduleResourceFilter(),
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=page_size),
            )
            objects += response.objects
            if len(response.objects) < page_size:
                break
            page_size += 1

        return [{'id': o.id, 'name': o.name} for o in objects]

    @cachify('kaltura/get_canvas_category_object')
    def get_canvas_category_object(self, canvas_course_site_id):
        response = self.kaltura_client.category.list(
            filter=KalturaCategoryFilter(fullNameEqual=f'Canvas>site>channels>{canvas_course_site_id}'),
            pager=KalturaFilterPager(),
        )
        canvas_category_objects = [_category_object_to_json(o) for o in response.objects]
        return canvas_category_objects[0] if canvas_category_objects else None

    @cachify('kaltura/get_canvas_category_objects', timeout=30)
    def get_canvas_category_objects(self):
        objects = []
        page_index, page_size = 1, 200
        while page_index < MAX_PAGE:
            # TODO: In the long term, this won't scale well. Can we query by term?
            full_name_prefix = 'Canvas>site>channels>'
            response = self.kaltura_client.category.list(
                filter=KalturaCategoryFilter(fullNameStartsWith=full_name_prefix),
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=page_size),
            )
            objects += response.objects
            if len(response.objects) < page_size:
                break
            page_size += 1

        return [_category_object_to_json(o) for o in objects if o.fullName == f'{full_name_prefix}{o.name}']

    @skip_when_pytest(mock_object=int(datetime.now().timestamp()))
    def schedule_recording(
            self,
            course_label,
            instructors,
            days,
            start_time,
            end_time,
            publish_type,
            recording_type,
            room,
            term_id,
    ):
        kaltura_schedule = self._schedule_recurring_events_in_kaltura(
            course_label,
            instructors,
            days,
            start_time,
            end_time,
            publish_type,
            recording_type,
            room,
            term_id,
        )
        # Link the schedule to the room (ie, capture agent)
        self._attach_scheduled_recordings_to_room(kaltura_schedule=kaltura_schedule, room=room)
        return kaltura_schedule.id

    @skip_when_pytest()
    def add_scheduled_event_to_category(self, kaltura_schedule_id, category_object):
        # TODO: Kaltura API call to map scheduled recordings to canvas_category_object
        pass

    def ping(self):
        filter_ = KalturaMediaEntryFilter()
        filter_.nameLike = 'Love is the drug I\'m thinking of'
        result = self.kaltura_client.media.list(
            filter=filter_,
            pager=KalturaFilterPager(pageSize=1),
        )
        return result.totalCount is not None

    @property
    def kaltura_client(self):
        admin_secret = app.config['KALTURA_ADMIN_SECRET']
        unique_user_id = app.config['KALTURA_UNIQUE_USER_ID']
        partner_id = self.kaltura_partner_id
        expiry = app.config['KALTURA_EXPIRY']

        config = KalturaConfiguration()
        client = KalturaClient(config)
        ks = client.session.start(
            admin_secret,
            unique_user_id,
            KalturaSessionType.ADMIN,
            partner_id,
            expiry,
            'appId:appName-appDomain',
        )
        client.setKs(ks)
        return client

    def _schedule_recurring_events_in_kaltura(
            self,
            course_label,
            instructors,
            days,
            start_time,
            end_time,
            publish_type,
            recording_type,
            room,
            term_id,
    ):
        term_name = term_name_for_sis_id(term_id)
        term_end = datetime.strptime(app.config['CURRENT_TERM_END'], '%Y-%m-%d')

        summary = f'{course_label} ({term_name})'
        description = f"""
            {course_label} ({term_name}) meets in {room.location},
            between {start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}, on {days}.
            Recordings of type {recording_type} will be published to {publish_type}.
        """
        app.logger.info(description)

        first_day_start = get_first_matching_datetime_of_term(
            meeting_days=days,
            time_hours=start_time.hour,
            time_minutes=start_time.minute,
        )
        first_day_end = get_first_matching_datetime_of_term(
            meeting_days=days,
            time_hours=end_time.hour,
            time_minutes=end_time.minute,
        )
        recurring_event = KalturaRecordScheduleEvent(
            # https://developer.kaltura.com/api-docs/General_Objects/Objects/KalturaScheduleEvent
            classificationType=KalturaScheduleEventClassificationType.PUBLIC_EVENT,
            comment=f'{summary} recordings scheduled by Diablo on {to_isoformat(datetime.now())}',
            contact=','.join(instructor['uid'] for instructor in instructors),
            description=description.strip(),
            duration=(end_time - start_time).seconds,
            endDate=first_day_end.timestamp(),
            geoLatitude=None,  # TODO: Kaltura API did not like: 37.871853,
            geoLongitude=None,  # TODO: Kaltura API did not like: -122.258423,
            location=None,  # Room is assigned below with 'scheduleEventResource.add'.
            organizer=app.config['KALTURA_EVENT_ORGANIZER'],
            ownerId=app.config['KALTURA_KMS_OWNER_ID'],
            parentId=None,
            partnerId=self.kaltura_partner_id,
            priority=None,
            recurrence=KalturaScheduleEventRecurrence(
                # https://developer.kaltura.com/api-docs/General_Objects/Objects/KalturaScheduleEventRecurrence
                byDay=','.join(days),
                byHour=None,
                byMinute=None,
                byMonth=None,
                byMonthDay=None,
                byOffset=None,
                bySecond=None,
                byWeekNumber=None,
                byYearDay=None,
                count=None,
                frequency=KalturaScheduleEventRecurrenceFrequency.WEEKLY,
                # 'interval' is not documented. When scheduling manually, the value was 1 in each individual event.
                interval=1,
                name=summary,
                timeZone='US/Pacific',
                until=term_end.replace(hour=23, minute=59).timestamp(),
                weekStartDay=days[0],  # See KalturaScheduleEventRecurrenceDay enum
            ),
            recurrenceType=KalturaScheduleEventRecurrenceType.RECURRING,
            referenceId=None,
            sequence=None,
            startDate=first_day_start.timestamp(),
            status=KalturaScheduleEventStatus.ACTIVE,
            summary=summary,
            tags=None,
            templateEntryId=app.config['KALTURA_TEMPLATE_ENTRY_ID'],
        )
        return self.kaltura_client.schedule.scheduleEvent.add(recurring_event)

    def _attach_scheduled_recordings_to_room(self, kaltura_schedule, room):
        utc_now_timestamp = int(datetime.utcnow().timestamp())
        event_resource = self.kaltura_client.schedule.scheduleEventResource.add(
            KalturaScheduleEventResource(
                eventId=kaltura_schedule.id,
                resourceId=room.kaltura_resource_id,
                partnerId=self.kaltura_partner_id,
                createdAt=utc_now_timestamp,
                updatedAt=utc_now_timestamp,
            ),
        )
        app.logger.info(f'Kaltura schedule {kaltura_schedule.id} attached to {room.location}: {event_resource}')


def _category_object_to_json(obj):
    return {
        'id': obj.id,
        'courseSiteId': obj.name,
    }
