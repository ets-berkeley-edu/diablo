<template>
  <div v-if="!loading">
    <v-card outlined class="elevation-1">
      <v-card-title class="pb-0">
        <PageTitle icon="mdi-home-city-outline" :text="room.location" />
      </v-card-title>
      <v-card-actions>
        <v-list class="w-100" dense>
          <v-list-item v-if="room.kalturaResourceId">
            <div class="subtitle-1">
              Kaltura resource ID: {{ room.kalturaResourceId }}
              <span v-if="kalturaEventList">
                (<a id="skip-to-kaltura-event-list" @keypress="scrollToKalturaEvents" @click="scrollToKalturaEvents">Scroll to Kaltura events</a>)
              </span>
            </div>
          </v-list-item>
          <v-list-item>
            <div class="align-end d-flex w-100">
              <div class="pb-4 pr-3">
                <label for="select-room-capability" class="subtitle-1">Capability:</label>
              </div>
              <div>
                <SelectRoomCapability
                  :on-update="onUpdateRoomCapability"
                  :options="$config.roomCapabilityOptions"
                  :room="room"
                />
              </div>
              <div class="ml-auto">
                <v-switch v-model="isAuditorium" label="Auditorium"></v-switch>
              </div>
            </div>
          </v-list-item>
          <v-list-item v-if="offerPrintable">
            <router-link
              :id="`print-room-${room.id}-schedule`"
              aria-label="Open printable version of this page, in a new window"
              class="subtitle-1"
              target="_blank"
              :to="`/room/printable/${room.id}`"
            >
              <v-icon class="linked-icon">mdi-printer</v-icon> Print schedule<span class="sr-only"> (opens a new browser tab)</span>
            </router-link>
          </v-list-item>
        </v-list>
      </v-card-actions>
      <v-card-text>
        <CoursesDataTable
          :courses="room.courses"
          :include-room-column="false"
          :message-for-courses="summarize(room.courses)"
          :on-toggle-opt-out="() => {}"
          :refreshing="false"
        />
      </v-card-text>
    </v-card>
    <div v-if="kalturaEventList" class="ma-3 pt-5">
      <h2>Kaltura Events in {{ room.location }}</h2>
      <KalturaEventList :events="kalturaEventList" />
    </div>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import CoursesDataTable from '@/components/course/CoursesDataTable'
  import KalturaEventList from '@/components/kaltura/KalturaEventList'
  import PageTitle from '@/components/util/PageTitle'
  import SelectRoomCapability from '@/components/room/SelectRoomCapability'
  import Utils from '@/mixins/Utils'
  import {getKalturaEventList, getRoom, setAuditorium} from '@/api/room'

  export default {
    name: 'Room',
    mixins: [Context, Utils],
    components: {KalturaEventList, CoursesDataTable, PageTitle, SelectRoomCapability},
    data: () => ({
      isAuditorium: undefined,
      kalturaEventList: undefined,
      offerPrintable: undefined,
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
      let roomId = this.$_.get(this.$route, 'params.id')
      getRoom(roomId).then(data => {
        this.room = data
        this.isAuditorium = data.isAuditorium
        this.$_.each(this.room.courses, course => {
          course.courseCodes = this.getCourseCodes(course)
        })
        this.offerPrintable = !!this.$_.find(this.$_.filter(this.room.courses, 'scheduled'), c => c.scheduled.room.id === this.room.id)
        this.$ready(data.location)
        // The page is ready; Kaltura events will pop up in a sec.
        if (this.room.kalturaResourceId) {
          getKalturaEventList(this.room.kalturaResourceId).then(data => {
            this.kalturaEventList = data
          })
        }
      })
    },
    methods: {
      onUpdateRoomCapability(capability) {
        this.room.capability = capability
        this.alertScreenReader(capability ? `'${capability}' selected` : 'Room capability removed.')
      },
      scrollToKalturaEvents() {
        this.$vuetify.goTo('#kaltura-event-list', {duration: 300, offset: 100, easing: 'easeInOutCubic'})
        this.alertScreenReader('Scrolled to Kaltura events.')
      }
    }
  }
</script>
