<template>
  <div v-if="!loading">
    <h1><v-icon class="pb-2" large>mdi-domain</v-icon> {{ room.location }}</h1>
    <div v-if="room.kalturaResourceId" class="pa-3 subtitle-1">
      Kaltura resource ID: {{ room.kalturaResourceId }}
      <span v-if="kalturaEventList">
        (<a id="skip-to-kaltura-event-list" @keypress="scrollToKalturaEvents" @click="scrollToKalturaEvents">Scroll to Kaltura events</a>)
      </span>
    </div>
    <v-card outlined class="elevation-1">
      <v-list-item three-line class="ma-2">
        <v-list-item-content>
          <div class="align-start overline w-50 d-flex">
            <div class="pr-3 pt-1">
              <label for="select-room-capability" class="subtitle-1">Capability:</label>
            </div>
            <div>
              <SelectRoomCapability
                :is-auditorium="room.isAuditorium"
                :on-update="onUpdateRoomCapability"
                :options="$config.roomCapabilityOptions"
                :room="room"
              />
            </div>
            <div class="ml-auto">
              <v-switch v-model="isAuditorium" label="Auditorium"></v-switch>
            </div>
          </div>
          <v-list-item-title>
            <span v-if="scheduledCourses.length">
              <router-link
                :id="`print-room-${room.id}-schedule`"
                class="subtitle-1"
                target="_blank"
                :to="`/room/printable/${room.id}`"
              >
                <v-icon class="linked-icon">mdi-printer</v-icon> Print schedule<span class="sr-only"> (opens a new browser tab)</span>
              </router-link>
            </span>
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <CoursesDataTable
        :courses="room.courses"
        :include-room-column="false"
        :message-for-courses="getMessageForCourses()"
        :on-toggle-opt-out="() => {}"
        :refreshing="false"
      />
    </v-card>
    <div v-if="kalturaEventList" class="ma-3 pt-5">
      <h2>Kaltura Events in {{ room.location }}</h2>
      <v-data-table
        id="kaltura-event-list"
        class="elevation-1 mt-3"
        disable-pagination
        :headers="kalturaEventListHeaders"
        hide-default-footer
        item-key="id"
        :items="kalturaEventList"
        show-expand
        :single-expand="true"
      >
        <template v-slot:item.startDate="{ item }">
          <span v-if="item.startDate" class="text-no-wrap">
            {{ item.startDate | moment('ddd, MMM D, YYYY') }}
          </span>
        </template>
        <template v-slot:item.endDate="{ item }">
          <span v-if="item.endDate" class="text-no-wrap">
            {{ item.endDate | moment('ddd, MMM D, YYYY') }}
          </span>
        </template>
        <template v-slot:item.duration="{ item }">
          <span v-if="item.duration" class="text-no-wrap">
            {{ [item.duration, 'seconds'] | duration('as', 'hours') }} hours
          </span>
        </template>
        <template v-slot:item.days="{ item }">
          {{ $_.get(item.recurrence, 'byDay') || '&mdash;' }}
        </template>
        <template v-slot:expanded-item="{ headers, item }">
          <td :colspan="headers.length">
            <div v-if="item.children" class="ma-5">
              <div class="title">
                Series
              </div>
              <v-simple-table>
                <template v-slot:default>
                  <thead>
                    <tr>
                      <th class="text-left">Parent Id</th>
                      <th class="text-left">Id</th>
                      <th class="text-left">Start</th>
                      <th class="text-left">End</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="event in item.children" :key="event.id">
                      <td>{{ event.parentId }}</td>
                      <td>{{ event.id }}</td>
                      <td>{{ event.startDate | moment('h:mma, ddd, MMM D') }}</td>
                      <td>{{ event.endDate | moment('h:mma, ddd, MMM D') }}</td>
                    </tr>
                  </tbody>
                </template>
              </v-simple-table>
              <div class="ma-5">
                <v-dialog v-model="rawJsonDialog[item.id]">
                  <template v-slot:activator="{ on }">
                    <v-btn color="accent" dark v-on="on">
                      <v-icon :id="`kaltura-event-{item.id}-children`" v-on="on" class="pr-3">
                        mdi-code-json
                      </v-icon> Raw JSON
                    </v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline grey lighten-2" primary-title>
                      Raw JSON of Event {{ item.id }} Children
                    </v-card-title>
                    <v-card-text>
                      <pre>{{ item.children }}</pre>
                    </v-card-text>
                    <v-divider></v-divider>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn
                        color="primary"
                        text
                        @click="rawJsonDialog[item.id] = false"
                      >
                        Close
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
              </div>
            </div>
            <pre v-if="!item.children">
              {{ item }}
            </pre>
          </td>
        </template>
      </v-data-table>
    </div>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import CoursesDataTable from '@/components/course/CoursesDataTable'
  import SelectRoomCapability from '@/components/room/SelectRoomCapability'
  import Utils from '@/mixins/Utils'
  import {getKalturaEventList, getRoom, setAuditorium} from '@/api/room'

  export default {
    name: 'Room',
    components: {CoursesDataTable, SelectRoomCapability},
    mixins: [Context, Utils],
    data: () => ({
      isAuditorium: undefined,
      kalturaEventList: undefined,
      kalturaEventListHeaders: [
          { text: 'Id', value: 'id' },
          { text: 'Summary', value: 'summary', sortable: false, class: 'w-30' },
          { text: 'Start', value: 'startDate', sortable: false },
          { text: 'End', value: 'endDate', sortable: false },
          { text: 'Duration', value: 'duration', sortable: false },
          { text: 'Days', value: 'days', sortable: false }
      ],
      scheduledCourses: undefined,
      rawJsonDialog: {},
      room: undefined
    }),
    watch: {
      isAuditorium(value) {
        if (!this.loading) {
          setAuditorium(this.room.id, value).then(() => {
            this.room.isAuditorium = value
          })
        }
      }
    },
    created() {
      this.$loading()
      let id = this.$_.get(this.$route, 'params.id')
      getRoom(id).then(data => {
        this.room = data
        this.isAuditorium = data.isAuditorium
        this.scheduledCourses = this.$_.filter(data.courses, 'scheduled')
        this.setPageTitle(data.location)
        if (this.room.kalturaResourceId) {
          getKalturaEventList(this.room.id).then(data => {
            this.kalturaEventList = data
            this.$ready()
          })
        } else {
          this.$ready()
        }
      }).catch(this.$ready)
    },
    methods: {
      getMessageForCourses() {
        return this.summarize(this.room.courses)
      },
      onUpdateRoomCapability(capability) {
        this.room.capability = capability
      },
      scrollToKalturaEvents() {
        this.$vuetify.goTo('#kaltura-event-list', {duration: 300, offset: 100, easing: 'easeInOutCubic'})
      },
      tdClass(course) {
        return course.approvals.length ? 'border-bottom-zero text-no-wrap' : 'text-no-wrap'
      }
    }
  }
</script>
