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
    no-data-text="No Kaltura events."
  >
    <template #item.summary="{item}">
      <a
        :id="`kaltura-media-space-${item.id}`"
        aria-label="Open Kaltura MediaSpace in a new window"
        :href="`${contextStore.config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${item.id}`"
        target="_blank"
      >
        {{ item.summary }} <v-icon class="ml-1" :icon="mdiOpenInNew" size="14" />
      </a>
    </template>
    <template #item.startDate="{item}">
      <span v-if="item.startDate" class="text-no-wrap">
        {{ formatDate(item.startDate, DateTime.DATE_MED_WITH_WEEKDAY) }}
      </span>
    </template>
    <template #item.endDate="{item}">
      <span v-if="get(item, 'recurrence.until')" class="text-no-wrap">
        {{ formatDate(item.recurrence.until, DateTime.DATE_MED_WITH_WEEKDAY) }}
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
      ></v-btn>
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
                    <a
                      :id="`kaltura-recurrence-${event.id}`"
                      :aria-label="`Open Kaltura MediaSpace in a new window (event ${event.id})`"
                      :href="`${contextStore.config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${event.id}`"
                      target="_blank"
                    >
                      {{ event.id }} <v-icon class="ml-1" :icon="mdiOpenInNew" size="14" />
                    </a>
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
                  <span v-if="endsWith(key, 'Date')">{{ formatDate(item[key], DateTime.DATE_MED) }}</span>
                  <div v-if="!endsWith(key, 'Date')">
                    <span v-if="key === 'id'">
                      <a
                        :id="`kaltura-event-${item[key]}`"
                        :aria-label="`Open Kaltura MediaSpace in a new window (event ${item[key]})`"
                        :href="`${contextStore.config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${item[key]}`"
                        target="_blank"
                      >
                        {{ item[key] }} <v-icon class="pl-2" :icon="mdiOpenInNew" size="small" />
                      </a>
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
import {mdiChevronDown, mdiChevronUp, mdiOpenInNew} from '@mdi/js'
import {useContextStore} from '@/stores/context'

defineProps({
  events: {
    required: true,
    type: Array
  },
  location: {
    required: true,
    type: String
  }
})

const contextStore = useContextStore()

const formatDate = (date, format) => {
  return DateTime.fromISO(date).toLocaleString(format)
}

const formatDateTime = date => {
  return DateTime.fromISO(date).toFormat('h:mm a, EEE, MMM d')
}
</script>
