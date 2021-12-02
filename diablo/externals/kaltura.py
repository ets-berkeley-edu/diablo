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
from datetime import date, datetime, time, timedelta
import hashlib
import json

import dateutil.parser
from diablo import cachify, skip_when_pytest
from diablo.lib.berkeley import get_first_matching_datetime_of_term, get_recording_end_date, get_recording_start_date, \
    term_name_for_sis_id
from diablo.lib.kaltura_util import get_classification_name, get_recurrence_name, get_series_description, \
    get_status_name, represents_recording_series
from diablo.lib.util import default_timezone, epoch_time_to_isoformat, format_days
from flask import current_app as app
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Core import KalturaBaseEntry, KalturaCategoryEntry, KalturaCategoryEntryFilter, \
    KalturaCategoryEntryStatus, KalturaCategoryFilter, KalturaEntryDisplayInSearchType, KalturaEntryModerationStatus, \
    KalturaEntryStatus, KalturaEntryType, KalturaFilterPager, KalturaMediaEntryFilter
from KalturaClient.Plugins.Schedule import KalturaRecordScheduleEvent, KalturaRecordScheduleEventFilter, \
    KalturaScheduleEventClassificationType, KalturaScheduleEventFilter, KalturaScheduleEventRecurrence, \
    KalturaScheduleEventRecurrenceFrequency, KalturaScheduleEventRecurrenceType, KalturaScheduleEventResource, \
    KalturaScheduleEventStatus, KalturaScheduleResourceFilter, KalturaSessionType

CREATED_BY_DIABLO_TAG = 'ets_course_capture'

DEFAULT_KALTURA_PAGE_SIZE = 200


class Kaltura:

    @skip_when_pytest()
    def __init__(self):
        expiry = app.config['KALTURA_EXPIRY']
        partner_id = app.config['KALTURA_PARTNER_ID']

        self.client = KalturaClient(KalturaConfiguration())
        result = self.client.session.startWidgetSession(
            expiry=expiry,
            widgetId=f'_{partner_id}',
        )
        self.client.setKs(result.ks)

        token_hash = hashlib.sha256((result.ks + app.config['KALTURA_APP_TOKEN']).encode('ascii')).hexdigest()
        result = self.client.appToken.startSession(
            expiry=expiry,
            id=app.config['KALTURA_APP_TOKEN_ID'],
            tokenHash=token_hash,
            type=KalturaSessionType.ADMIN,
        )
        self.client.setKs(result.ks)

    @skip_when_pytest()
    def add_to_kaltura_category(self, category_id, entry_id):
        category_entry_user_id = 'RecordScheduleGroup'  # TODO: Does this need to be be configurable? Probably.
        category_entry = KalturaCategoryEntry(
            categoryId=category_id,
            entryId=entry_id,
            status=KalturaCategoryEntryStatus.ACTIVE,
            creatorUserId=category_entry_user_id,
        )
        self.client.categoryEntry.add(category_entry)

    @skip_when_pytest()
    def get_base_entry(self, entry_id):
        entry = self.client.baseEntry.get(entryId=entry_id)
        if entry:
            return {
                'createdAt': entry.createdAt,
                'creatorId': entry.creatorId,
                'description': entry.description,
                'displayInSearch': entry.displayInSearch,
                'entitledUsersEdit': entry.entitledUsersEdit,
                'entitledUsersPublish': entry.entitledUsersPublish,
                'entitledUsersView': entry.entitledUsersView,
                'id': entry.id,
                'name': entry.name,
                'partnerId': entry.partnerId,
                'status': entry.status,
                'tags': entry.tags,
                'updatedAt': entry.updatedAt,
                'userId': entry.userId,
            }
        else:
            return None

    @skip_when_pytest()
    def get_categories(self, template_entry_id):
        category_entries = self._get_category_entries(KalturaCategoryEntryFilter(entryIdEqual=template_entry_id))
        if category_entries:
            category_ids = [entry['categoryId'] for entry in category_entries]
            category_filter = KalturaCategoryFilter(idIn=','.join(str(id_) for id_ in category_ids))
            return self._get_categories(kaltura_category_filter=category_filter)
        else:
            return []

    @skip_when_pytest()
    def get_events_by_location(self, kaltura_resource_id):
        event_filter = KalturaScheduleEventFilter(
            orderBy='-startDate',
            resourceIdEqual=str(kaltura_resource_id),
        )
        return self._get_events(kaltura_event_filter=event_filter)

    @skip_when_pytest()
    def get_events_by_tag(self, tags_like=CREATED_BY_DIABLO_TAG):
        return self._get_events(kaltura_event_filter=KalturaScheduleEventFilter(tagsLike=tags_like))

    @skip_when_pytest()
    def get_event(self, event_id):
        events = self._get_events(kaltura_event_filter=KalturaScheduleEventFilter(idEqual=event_id))
        return events[0] if events else None

    @skip_when_pytest()
    def get_events_in_date_range(self, end_date, start_date, recurrence_type=None):
        end_date_timestamp = int(end_date.timestamp())
        start_date_timestamp = int(start_date.timestamp())
        if recurrence_type is None:
            event_filter = KalturaRecordScheduleEventFilter(
                endDateLessThanOrEqual=end_date_timestamp,
                startDateGreaterThanOrEqual=start_date_timestamp,
            )
        else:
            event_filter = KalturaRecordScheduleEventFilter(
                endDateLessThanOrEqual=end_date_timestamp,
                recurrenceTypeEqual=recurrence_type,
                startDateGreaterThanOrEqual=start_date_timestamp,
            )
        return self._get_events(kaltura_event_filter=event_filter)

    @cachify('kaltura/schedule_resources', timeout=30)
    def get_schedule_resources(self):
        def _fetch(page_index):
            return self.client.schedule.scheduleResource.list(
                filter=KalturaScheduleResourceFilter(),
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=DEFAULT_KALTURA_PAGE_SIZE),
            )
        return [{'id': o.id, 'name': o.name} for o in _get_kaltura_objects(_fetch)]

    @skip_when_pytest()
    def get_canvas_category_object(self, canvas_course_site_id):
        return self.get_category_object(name=f'Canvas>site>channels>{canvas_course_site_id}')

    @skip_when_pytest()
    def get_category_object(self, name):
        response = self.client.category.list(
            filter=KalturaCategoryFilter(fullNameEqual=name),
            pager=KalturaFilterPager(pageIndex=1, pageSize=1),
        )
        category_objects = [_category_object_to_json(o) for o in response.objects]
        return category_objects[0] if category_objects else None

    @skip_when_pytest(mock_object=int(datetime.now().timestamp()))
    def schedule_recording(
            self,
            canvas_course_site_ids,
            course_label,
            instructors,
            meeting,
            publish_type,
            recording_type,
            room,
            term_id,
    ):
        category_ids = []
        common_category = self.get_category_object(name=app.config['KALTURA_COMMON_CATEGORY'])
        if common_category:
            category_ids.append(common_category['id'])

        if publish_type == 'kaltura_media_gallery':
            for canvas_course_site_id in canvas_course_site_ids:
                category = self.get_canvas_category_object(canvas_course_site_id=canvas_course_site_id)
                if category:
                    category_ids.append(category['id'])

        kaltura_schedule = self._schedule_recurring_events_in_kaltura(
            category_ids=category_ids,
            course_label=course_label,
            instructors=instructors,
            meeting=meeting,
            publish_type=publish_type,
            recording_type=recording_type,
            room=room,
            term_id=term_id,
        )
        recurrences_filter = KalturaScheduleEventFilter(parentIdEqual=kaltura_schedule.id)
        for recurrence in self._get_events(kaltura_event_filter=recurrences_filter):
            if recurrence['blackoutConflicts']:
                self.client.schedule.scheduleEvent.cancel(recurrence['id'])
                app.logger.warn(f"""
                    {course_label}: Event {recurrence['id']}), a child of Kaltura series {kaltura_schedule.id},
                    cancelled due to blackout conflict(s): {recurrence['blackoutConflicts']}
                """)

        # Link the schedule to the room (ie, capture agent)
        self._attach_scheduled_recordings_to_room(kaltura_schedule=kaltura_schedule, room=room)
        return kaltura_schedule.id

    @skip_when_pytest()
    def delete(self, event_id):
        def is_future(kaltura_event):
            start_date = dateutil.parser.parse(kaltura_event['startDate'])
            return start_date.timestamp() > datetime.now().timestamp()

        event = self.get_event(event_id)
        if event:
            recurrence_type = event['recurrenceType']
            if recurrence_type == 'Recurring':
                # This is a Kaltura series event.
                if is_future(kaltura_event=event):
                    # Start date of the series in the future. Delete it all.
                    self.client.schedule.scheduleEvent.delete(event_id)
                else:
                    # Series started in the past. Delete only the future 'recurrences'.
                    recurrences_filter = KalturaScheduleEventFilter(parentIdEqual=event_id)
                    for recurrence in self._get_events(kaltura_event_filter=recurrences_filter):
                        if is_future(kaltura_event=recurrence):
                            self.client.schedule.scheduleEvent.cancel(recurrence['id'])
            elif recurrence_type == 'Recurrence':
                # Delete is not supported for "recurrence" events.
                self.client.schedule.scheduleEvent.cancel(event_id)
            else:
                # This is not a series event. Delete it, whatever it is.
                self.client.schedule.scheduleEvent.delete(event_id)

    def ping(self):
        filter_ = KalturaMediaEntryFilter()
        filter_.nameLike = "Love is the drug I'm thinking of"
        result = self.client.baseEntry.list(
            filter=filter_,
            pager=KalturaFilterPager(pageSize=1),
        )
        return result.totalCount is not None

    def update_base_entry(self, entitled_users, entry_id):
        self.client.baseEntry.update(
            entryId=entry_id,
            baseEntry=KalturaBaseEntry(entitledUsersEdit=','.join(_to_normalized_set(entitled_users))),
        )

    def _get_events(self, kaltura_event_filter):
        def _fetch(page_index):
            return self.client.schedule.scheduleEvent.list(
                filter=kaltura_event_filter,
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=DEFAULT_KALTURA_PAGE_SIZE),
            )
        return _events_to_api_json(_get_kaltura_objects(_fetch))

    def _get_categories(self, kaltura_category_filter):
        def _fetch(page_index):
            return self.client.category.list(
                filter=kaltura_category_filter,
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=DEFAULT_KALTURA_PAGE_SIZE),
            )
        return [_category_object_to_json(obj) for obj in _get_kaltura_objects(_fetch)]

    def _get_category_entries(self, kaltura_category_entry_filter):
        def _fetch(page_index):
            return self.client.categoryEntry.list(
                filter=kaltura_category_entry_filter,
                pager=KalturaFilterPager(pageIndex=page_index, pageSize=DEFAULT_KALTURA_PAGE_SIZE),
            )
        return [_category_entry_object_to_json(obj) for obj in _get_kaltura_objects(_fetch)]

    def _schedule_recurring_events_in_kaltura(
            self,
            category_ids,
            course_label,
            instructors,
            meeting,
            publish_type,
            recording_type,
            room,
            term_id,
    ):
        # Recording starts X minutes before/after official start; it ends Y minutes before/after official end time.
        days = format_days(meeting['days'])
        start_time = _adjust_time(meeting['startTime'], app.config['KALTURA_RECORDING_OFFSET_START'])
        end_time = _adjust_time(meeting['endTime'], app.config['KALTURA_RECORDING_OFFSET_END'])

        app.logger.info(f"""
            Prepare to schedule recordings for {course_label}:
                Room: {room.location}
                Instructor UIDs: {[instructor['uid'] for instructor in instructors]}
                Schedule: {days}, {start_time} to {end_time}
                Recording: {recording_type}; {publish_type}
        """)

        term_name = term_name_for_sis_id(term_id)
        recording_start_date = get_recording_start_date(meeting, return_today_if_past_start=True)
        recording_end_date = get_recording_end_date(meeting)
        summary = f'{course_label} ({term_name})'
        app.logger.info(f"""
            {course_label} ({term_name}) meets in {room.location},
            between {start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}, on {days}.
            Recordings of type {recording_type} will be published to {publish_type}.
        """)

        first_day_start = get_first_matching_datetime_of_term(
            meeting_days=days,
            start_date=recording_start_date,
            time_hours=start_time.hour,
            time_minutes=start_time.minute,
        )
        first_day_end = get_first_matching_datetime_of_term(
            meeting_days=days,
            start_date=recording_start_date,
            time_hours=end_time.hour,
            time_minutes=end_time.minute,
        )
        description = get_series_description(course_label, instructors, term_name)
        base_entry = self._create_kaltura_base_entry(
            description=description,
            instructors=instructors,
            name=f'{summary} in {room.location}',
        )
        for category_id in category_ids or []:
            self.add_to_kaltura_category(category_id=category_id, entry_id=base_entry.id)

        until = datetime.combine(
            recording_end_date,
            time(end_time.hour, end_time.minute),
            tzinfo=default_timezone(),
        )
        recurring_event = KalturaRecordScheduleEvent(
            # https://developer.kaltura.com/api-docs/General_Objects/Objects/KalturaScheduleEvent
            classificationType=KalturaScheduleEventClassificationType.PUBLIC_EVENT,
            comment=f'{summary} in {room.location}',
            contact=','.join(instructor['uid'] for instructor in instructors),
            description=description,
            duration=(end_time - start_time).seconds,
            endDate=first_day_end.timestamp(),
            organizer=app.config['KALTURA_EVENT_ORGANIZER'],
            ownerId=app.config['KALTURA_KMS_OWNER_ID'],
            partnerId=app.config['KALTURA_PARTNER_ID'],
            recurrence=KalturaScheduleEventRecurrence(
                # https://developer.kaltura.com/api-docs/General_Objects/Objects/KalturaScheduleEventRecurrence
                byDay=','.join(days),
                frequency=KalturaScheduleEventRecurrenceFrequency.WEEKLY,
                # 'interval' is not documented. When scheduling manually, the value was 1 in each individual event.
                interval=1,
                name=summary,
                timeZone='US/Pacific',
                until=until.timestamp(),
                weekStartDay=days[0],
            ),
            recurrenceType=KalturaScheduleEventRecurrenceType.RECURRING,
            startDate=first_day_start.timestamp(),
            status=KalturaScheduleEventStatus.ACTIVE,
            summary=summary,
            tags=CREATED_BY_DIABLO_TAG,
            templateEntryId=base_entry.id,
        )
        return self.client.schedule.scheduleEvent.add(recurring_event)

    def _create_kaltura_base_entry(
            self,
            description,
            name,
            instructors,
    ):
        instructor_uids = [instructor['uid'] for instructor in instructors]
        uids = ','.join(_to_normalized_set(instructor_uids)) if instructor_uids else None
        base_entry = KalturaBaseEntry(
            description=description,
            displayInSearch=KalturaEntryDisplayInSearchType.PARTNER_ONLY,
            entitledUsersEdit=uids,
            entitledUsersPublish=uids,
            moderationStatus=KalturaEntryModerationStatus.AUTO_APPROVED,
            name=name,
            partnerId=app.config['KALTURA_PARTNER_ID'],
            status=KalturaEntryStatus.NO_CONTENT,
            tags=CREATED_BY_DIABLO_TAG,
            type=KalturaEntryType.MEDIA_CLIP,
            userId='RecordScheduleGroup',
        )
        return self.client.baseEntry.add(base_entry)

    def _attach_scheduled_recordings_to_room(self, kaltura_schedule, room):
        utc_now_timestamp = int(datetime.utcnow().timestamp())
        event_resource = self.client.schedule.scheduleEventResource.add(
            KalturaScheduleEventResource(
                eventId=kaltura_schedule.id,
                resourceId=room.kaltura_resource_id,
                partnerId=app.config['KALTURA_PARTNER_ID'],
                createdAt=utc_now_timestamp,
                updatedAt=utc_now_timestamp,
            ),
        )
        app.logger.info(f'Kaltura schedule {kaltura_schedule.id} attached to {room.location}: {event_resource}')


def _adjust_time(military_time, offset_minutes):
    hour_and_minutes = military_time.split(':')
    hour = int(hour_and_minutes[0])
    minutes = int(hour_and_minutes[1])
    return datetime.combine(
        date.today(),
        time(hour, minutes),
        tzinfo=default_timezone(),
    ) + timedelta(minutes=offset_minutes)


def _category_entry_object_to_json(obj):
    return {
        'categoryId': obj.categoryId,
        'status': obj.status,
    }


def _category_object_to_json(obj):
    return {
        'id': obj.id,
        'name': obj.name,
    }


def _get_kaltura_objects(_fetch):
    response = _fetch(1)
    total_count = response.totalCount
    objects = response.objects
    for page in range(2, int(total_count / DEFAULT_KALTURA_PAGE_SIZE) + 2):
        objects += _fetch(page).objects
    return objects


def _to_normalized_set(strings):
    return set([s.strip().lower() for s in strings])


def _events_to_api_json(events):
    # Time to organize. Find 'recurring' events and their corresponding 'recurrences'.
    recurring_events = []
    miscellanea = []
    for event in [_event_to_json(event) for event in events]:
        if represents_recording_series(event):
            recurring_events.append(event)
        else:
            miscellanea.append(event)

    for recurring_event in recurring_events:
        def _belongs_in_the_series(e):
            return e.get('recurrenceType', '').lower() == 'recurrence' and e.get('parentId') == recurring_event['id']
        # Find events of the series.
        recurrences = list(filter(lambda e: _belongs_in_the_series(e), miscellanea))
        recurring_event['recurrences'] = recurrences
        for recurrence in recurrences:
            # The 'recurrence' is removed from the generic list.
            miscellanea.remove(recurrence)
    return recurring_events + miscellanea


def _event_to_json(event):
    conflicts = [_blackout_to_json(e) for e in event.blackoutConflicts] if hasattr(event, 'blackoutConflicts') and event.blackoutConflicts else None
    api_json = {
        'blackoutConflicts': conflicts,
        'categoryIds': json.loads(event.categoryIds) if hasattr(event, 'categoryIds') and event.categoryIds else [],
        'classificationType': get_classification_name(event.classificationType),
        'comment': event.comment,
        'contact': event.contact,
        'createdAt': epoch_time_to_isoformat(event.createdAt),
        'description': event.description,
        'duration': event.duration,
        'durationFormatted': str(timedelta(seconds=event.duration)) if event.duration else None,
        'endDate': epoch_time_to_isoformat(event.endDate),
        'geoLatitude': event.geoLatitude,
        'geoLongitude': event.geoLongitude,
        'id': event.id,
        'location': event.location,
        'organizer': event.organizer,
        'ownerId': event.ownerId,
        'parentId': event.parentId,
        'partnerId': event.partnerId,
        'priority': event.priority,
        'recurrenceType': get_recurrence_name(event.recurrenceType),
        'referenceId': event.referenceId,
        'relatedObjects': event.relatedObjects,
        'sequence': event.sequence,
        'startDate': epoch_time_to_isoformat(event.startDate),
        'status': get_status_name(event.status),
        'summary': event.summary,
        'tags': event.tags,
        'templateEntryId': event.templateEntryId if hasattr(event, 'templateEntryId') else None,
        'updatedAt': epoch_time_to_isoformat(event.updatedAt),
    }
    if event.recurrence:
        api_json['recurrence'] = {
            'byDay': event.recurrence.byDay,
            'byHour': event.recurrence.byHour,
            'byMinute': event.recurrence.byMinute,
            'byMonth': event.recurrence.byMonth,
            'byMonthDay': event.recurrence.byMonthDay,
            'byOffset': event.recurrence.byOffset,
            'bySecond': event.recurrence.bySecond,
            'byWeekNumber': event.recurrence.byWeekNumber,
            'byYearDay': event.recurrence.byYearDay,
            'count': event.recurrence.count,
            'frequency': event.recurrence.frequency.value.capitalize(),
            'interval': event.recurrence.interval,
            'name': event.recurrence.name,
            'relatedObjects': event.recurrence.relatedObjects,
            'timeZone': event.recurrence.timeZone,
            'until': epoch_time_to_isoformat(event.recurrence.until),
        }
    return api_json


def _blackout_to_json(event):
    return {
        'classificationType': get_classification_name(event.classificationType),
        'comment': event.comment,
        'contact': event.contact,
        'createdAt': epoch_time_to_isoformat(event.createdAt),
        'description': event.description,
        'duration': event.duration,
        'durationFormatted': str(timedelta(seconds=event.duration)) if event.duration else None,
        'endDate': epoch_time_to_isoformat(event.endDate),
        'geoLatitude': event.geoLatitude,
        'geoLongitude': event.geoLongitude,
        'id': event.id,
        'organizer': event.organizer,
        'ownerId': event.ownerId,
        'partnerId': event.partnerId,
        'recurrenceType': get_recurrence_name(event.recurrenceType),
        'startDate': epoch_time_to_isoformat(event.startDate),
        'status': get_status_name(event.status),
        'summary': event.summary,
        'tags': event.tags,
        'updatedAt': epoch_time_to_isoformat(event.updatedAt),
    }
