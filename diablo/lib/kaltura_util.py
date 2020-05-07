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
from diablo.lib.util import epoch_time_to_isoformat
from KalturaClient.Plugins.Schedule import KalturaScheduleEventClassificationType, KalturaScheduleEventRecurrenceType, \
    KalturaScheduleEventStatus


def schedule_event_to_api_json(event):
    return {
        'blackoutConflicts': event.blackoutConflicts,
        'categoryIds': event.categoryIds,
        'classificationType': get_classification_name(event.classificationType),
        'comment': event.comment,
        'contact': event.contact,
        'createdAt': epoch_time_to_isoformat(event.createdAt),
        'description': event.description,
        'duration': event.duration,
        'endDate': epoch_time_to_isoformat(event.endDate),
        'entryIds': event.entryIds,
        'geoLatitude': event.geoLatitude,
        'geoLongitude': event.geoLongitude,
        'id': event.id,
        'location': event.location,
        'organizer': event.organizer,
        'ownerId': event.ownerId,
        'parentId': event.parentId,
        'partnerId': event.partnerId,
        'priority': event.priority,
        'recurrence': {
            'byDay': event.recurrence and event.recurrence.byDay,
            'byHour': event.recurrence and event.recurrence.byHour,
            'byMinute': event.recurrence and event.recurrence.byMinute,
            'byMonth': event.recurrence and event.recurrence.byMonth,
            'byMonthDay': event.recurrence and event.recurrence.byMonthDay,
            'byOffset': event.recurrence and event.recurrence.byOffset,
            'bySecond': event.recurrence and event.recurrence.bySecond,
            'byWeekNumber': event.recurrence and event.recurrence.byWeekNumber,
            'byYearDay': event.recurrence and event.recurrence.byYearDay,
            'count': event.recurrence and event.recurrence.count,
            'frequency': get_recurrence_frequency_name(event.recurrence),
            'interval': event.recurrence and event.recurrence.interval,
            'name': event.recurrence and event.recurrence.name,
            'relatedObjects': event.recurrence and event.recurrence.relatedObjects,
            'timeZone': event.recurrence and event.recurrence.timeZone,
            'until': event.recurrence and epoch_time_to_isoformat(event.recurrence.until),
        },
        'recurrenceType': get_recurrence_name(event.recurrenceType),
        'referenceId': event.referenceId,
        'relatedObjects': event.relatedObjects,
        'sequence': event.sequence,
        'startDate': epoch_time_to_isoformat(event.startDate),
        'status': get_status_name(event.status),
        'summary': event.summary,
        'tags': event.tags,
        'templateEntryId': event.templateEntryId,
        'updatedAt': epoch_time_to_isoformat(event.updatedAt),
    }


def get_classification_name(classification_type):
    return classification_type and {
        KalturaScheduleEventClassificationType.CONFIDENTIAL_EVENT: 'Confidential',
        KalturaScheduleEventClassificationType.PRIVATE_EVENT: 'Private',
        KalturaScheduleEventClassificationType.PUBLIC_EVENT: 'Public',
    }[classification_type.value]


def get_recurrence_name(recurrence_type):
    return recurrence_type and {
        KalturaScheduleEventRecurrenceType.NONE: 'None',
        KalturaScheduleEventRecurrenceType.RECURRENCE: 'Recurrence',
        KalturaScheduleEventRecurrenceType.RECURRING: 'Recurring',
    }[recurrence_type.value]


def get_status_name(status_type):
    return status_type and {
        KalturaScheduleEventStatus.ACTIVE: 'Active',
        KalturaScheduleEventStatus.CANCELLED: 'Canceled',
        KalturaScheduleEventStatus.DELETED: 'Deleted',
    }[status_type.value]


def get_recurrence_frequency_name(recurrence):
    return recurrence and recurrence.frequency.value.capitalize()
