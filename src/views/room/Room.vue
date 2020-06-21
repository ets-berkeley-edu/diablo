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
        :message-for-courses="summarize(room.courses)"
        :on-toggle-opt-out="() => {}"
        :refreshing="false"
      />
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
  import SelectRoomCapability from '@/components/room/SelectRoomCapability'
  import Utils from '@/mixins/Utils'
  import {getKalturaEventList, getRoom, setAuditorium} from '@/api/room'

  export default {
    name: 'Room',
    components: {KalturaEventList, CoursesDataTable, SelectRoomCapability},
    mixins: [Context, Utils],
    data: () => ({
      isAuditorium: undefined,
      kalturaEventList: undefined,
      scheduledCourses: undefined,
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
        this.$_.each(this.room.courses, course => {
          course.courseCodes = this.getCourseCodes(course)
        })
        this.scheduledCourses = this.$_.filter(data.courses, 'scheduled')
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
