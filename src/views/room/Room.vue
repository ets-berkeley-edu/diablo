<template>
  <div v-if="!loading">
    <div class="mb-3">
      <h1>{{ room.location }}</h1>
      <div v-if="room.kalturaResourceId" class="subtitle-1">
        Kaltura resource ID: {{ room.kalturaResourceId }}
      </div>
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
            <span v-if="room.courses.length">
              <router-link
                v-if="scheduledCourses.length"
                :id="`print-room-${room.id}-schedule`"
                class="subtitle-1"
                target="_blank"
                :to="`/room/printable/${room.id}`">
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
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import CoursesDataTable from '@/components/course/CoursesDataTable'
  import SelectRoomCapability from '@/components/room/SelectRoomCapability'
  import Utils from '@/mixins/Utils'
  import {getRoom, setAuditorium} from '@/api/room'

  export default {
    name: 'Room',
    components: {CoursesDataTable, SelectRoomCapability},
    mixins: [Context, Utils],
    data: () => ({
      isAuditorium: undefined,
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
        this.scheduledCourses = this.$_.filter(data.courses, 'scheduled')
        this.setPageTitle(data.location)
        this.$ready()
      }).catch(this.$ready)
    },
    methods: {
      getMessageForCourses() {
        return this.summarize(this.room.courses)
      },
      onUpdateRoomCapability(capability) {
        this.room.capability = capability
      },
      tdClass(course) {
        return course.approvals.length ? 'border-bottom-zero text-no-wrap' : 'text-no-wrap'
      }
    }
  }
</script>
