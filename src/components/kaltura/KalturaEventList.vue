<template>
  <v-data-table
    id="kaltura-event-list"
    disable-sort
    :header-props="{class: 'font-size-13 font-weight-bold text-medium-emphasis'}"
    :headers="[
      { title: '', value: 'data-table-expand', sortable: false, width: '24px' },
      {title: 'Id', value: 'id'},
      {title: 'Summary', value: 'summary', class: 'w-30'},
      {title: 'Start', value: 'startDate'},
      {title: 'End', value: 'endDate'},
      {title: 'Duration', value: 'duration'},
      {title: 'Days', value: 'days'}
    ]"
    hide-default-footer
    :items="events"
    :items-per-page="-1"
    :loading="isLoading"
    no-data-text="No Kaltura events."
  >
    <template #item.summary="{item}">
      <ExternalLink :href="`${contextStore.config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${item.id}`" :link-id="`kaltura-media-space-${item.id}`">
        {{ item.summary }}<span class="sr-only">&nbsp;Kaltura Events</span>
      </ExternalLink>
    </template>
    <template #item.startDate="{item}">
      <span v-if="item.startDate" class="text-no-wrap">
        <Date :date="item.startDate" :format="DateTime.DATE_MED_WITH_WEEKDAY" />
      </span>
    </template>
    <template #item.endDate="{item}">
      <span v-if="get(item, 'recurrence.until')" class="text-no-wrap">
        <Date :date="item.recurrence.until" :format="DateTime.DATE_MED_WITH_WEEKDAY" />
      </span>
      <span v-if="!get(item, 'recurrence.until')">
        &mdash;
      </span>
    </template>
    <template #item.duration="{item}">
      <span v-if="item.durationFormatted" class="text-no-wrap">
        {{ item.durationFormatted }}
      </span>
    </template>
    <template #item.days="{item}">
      <span aria-hidden="true">{{ get(item.recurrence, 'byDay') || '&mdash;' }}</span>
      <span class="sr-only">{{ get(item.recurrence, 'byDay') || 'blank' }}</span>
    </template>
    <template #item.data-table-expand="{ internalItem, isExpanded, toggleExpand }">
      <v-btn
        :id="`expand-kaltura-event-${internalItem.raw.id}`"
        :aria-expanded="isExpanded(internalItem)"
        :aria-label="`Kaltura events for ${internalItem.raw.summary}`"
        :icon="isExpanded(internalItem) ? mdiChevronUp : mdiChevronDown"
        slim
        variant="text"
        @click="toggleExpand(internalItem)"
      />
    </template>
    <template #expanded-row="{columns, item}">
      <tr>
        <td :colspan="columns.length">
          <div v-if="item.recurrences" class="pa-5">
            <div class="text-h6">Series</div>
            <v-table class="w-100">
              <thead>
                <tr>
                  <th class="font-size-13 font-weight-bold text-medium-emphasis">Id</th>
                  <th class="font-size-13 font-weight-bold text-medium-emphasis">Start</th>
                  <th class="font-size-13 font-weight-bold text-medium-emphasis">End</th>
                  <th class="font-size-13 font-weight-bold text-medium-emphasis">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in item.recurrences" :key="event.id">
                  <td>
                    <ExternalLink :href="`${contextStore.config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${event.id}`" :link-id="`kaltura-recurrence-${event.id}`">
                      <span class="sr-only">Kaltura event&nbsp;</span>{{ event.id }}
                    </ExternalLink>
                  </td>
                  <td>{{ formatDateTime(event.startDate) }}</td>
                  <td>{{ formatDateTime(event.endDate) }}</td>
                  <td>{{ event.status }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>
          <table v-if="!item.recurrences" class="ma-5">
            <thead>
              <tr>
                <th class="text-left">Key</th>
                <th class="text-left">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="key in ['id', 'summary', 'description', 'endDate', 'startDate', 'durationFormatted', 'status', 'classificationType']" :key="key">
                <td class="w-30">{{ key }}</td>
                <td v-if="item[key]">
                  <Date v-if="endsWith(key, 'Date')" :date="item[key]" />
                  <div v-if="!endsWith(key, 'Date')">
                    <span v-if="key === 'id'">
                      <ExternalLink :href="`${contextStore.config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${item[key]}`" :link-id="`kaltura-event-${item[key]}`">
                        <span class="sr-only">Kaltura event&nbsp;</span>{{ item[key] }}
                      </ExternalLink>
                    </span>
                    <span v-if="key !== 'id'">{{ item[key] }}</span>
                  </div>
                </td>
                <td v-if="!item[key]">&mdash;</td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>
    </template>
  </v-data-table>
</template>

<script setup>
import {DateTime} from 'luxon'
import {endsWith, get} from 'lodash'
import {mdiChevronDown, mdiChevronUp} from '@mdi/js'
import Date from '@/components/util/Date'
import ExternalLink from '@/components/util/ExternalLink'
import {useContextStore} from '@/stores/context'

defineProps({
  events: {
    required: true,
    type: Array
  },
  isLoading: {
    required: true,
    type: Boolean
  },
  location: {
    required: true,
    type: String
  }
})

const contextStore = useContextStore()

const formatDateTime = date => {
  return DateTime.fromISO(date).toFormat('h:mm a, EEE, MMM d')
}
</script>
