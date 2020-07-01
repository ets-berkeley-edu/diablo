<template>
  <v-data-table
    id="kaltura-event-list"
    class="elevation-1 mt-3"
    disable-pagination
    :headers="headers"
    hide-default-footer
    item-key="id"
    :items="events"
    show-expand
    :single-expand="true"
  >
    <template v-slot:item.summary="{ item }">
      <a
        :id="`kaltura-media-space-${item.id}`"
        :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${item.id}`"
        target="_blank"
        aria-label="Open Kaltura MediaSpace in a new window"
      >
        {{ item.summary }} <v-icon small class="pl-2">mdi-open-in-new</v-icon>
      </a>
    </template>
    <template v-slot:item.startDate="{ item }">
      <span v-if="item.startDate" class="text-no-wrap">
        {{ item.startDate | moment('ddd, MMM D, YYYY') }}
      </span>
    </template>
    <template v-slot:item.endDate="{ item }">
      <span v-if="$_.get(item, 'recurrence.until')" class="text-no-wrap">
        {{ item.recurrence.until | moment('ddd, MMM D, YYYY') }}
      </span>
      <span v-if="!$_.get(item, 'recurrence.until')">
        &mdash;
      </span>
    </template>
    <template v-slot:item.duration="{ item }">
      <span v-if="item.durationFormatted" class="text-no-wrap">
        {{ item.durationFormatted }}
      </span>
    </template>
    <template v-slot:item.days="{ item }">
      {{ $_.get(item.recurrence, 'byDay') || '&mdash;' }}
    </template>
    <template v-slot:expanded-item="{ headers, item }">
      <td :colspan="headers.length">
        <div v-if="item.recurrences" class="ma-5">
          <div class="title">
            Series
          </div>
          <v-simple-table>
            <template v-slot:default>
              <thead>
                <tr>
                  <th class="text-left">Id</th>
                  <th class="text-left">Start</th>
                  <th class="text-left">End</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in item.recurrences" :key="event.id">
                  <td>
                    <v-tooltip v-if="$_.size(event.blackoutConflicts)" :id="`blackout-conflicts-${event.id}`" top>
                      <template v-slot:activator="{ on }">
                        <v-icon
                          color="red"
                          class="pa-0"
                          v-on="on"
                        >
                          mdi-alert
                        </v-icon>
                      </template>
                      Event has blackout-conflict:
                      <pre>
                        {{ event.blackoutConflicts }}
                      </pre>
                    </v-tooltip>
                    <a
                      :id="`kaltura-recurrence-${event.id}`"
                      :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${event.id}`"
                      target="_blank"
                      :aria-label="`Open Kaltura MediaSpace in a new window (event ${event.id})`"
                    >
                      {{ event.id }} <v-icon small class="pl-2">mdi-open-in-new</v-icon>
                    </a>
                  </td>
                  <td>{{ event.startDate | moment('h:mma, ddd, MMM D') }}</td>
                  <td>{{ event.endDate | moment('h:mma, ddd, MMM D') }}</td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </div>
        <v-simple-table v-if="!item.recurrences" class="ma-5">
          <template v-slot:default>
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
                  <span v-if="$_.endsWith(key, 'Date')">{{ item[key] | moment('MMM D, YYYY') }}</span>
                  <div v-if="!$_.endsWith(key, 'Date')">
                    <span v-if="key === 'id'">
                      <a
                        :id="`kaltura-event-${item[key]}`"
                        :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${item[key]}`"
                        target="_blank"
                        :aria-label="`Open Kaltura MediaSpace in a new window (event ${item[key]})`"
                      >
                        {{ item[key] }} <v-icon small class="pl-2">mdi-open-in-new</v-icon>
                      </a>
                    </span>
                    <span v-if="key !== 'id'">{{ item[key] }}</span>
                  </div>
                </td>
                <td v-if="!item[key]">&mdash;</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </td>
    </template>
  </v-data-table>
</template>

<script>
  export default {
    name: 'KalturaEventList',
    props: {
      events: {
        required: true,
        type: Array
      }
    },
    data: () => ({
      headers: [
          { text: 'Id', value: 'id' },
          { text: 'Summary', value: 'summary', sortable: false, class: 'w-30' },
          { text: 'Start', value: 'startDate', sortable: false },
          { text: 'End', value: 'endDate', sortable: false },
          { text: 'Duration', value: 'duration', sortable: false },
          { text: 'Days', value: 'days', sortable: false }
      ]
    }),
  }
</script>
