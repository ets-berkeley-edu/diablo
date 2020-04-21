<template>
  <div v-if="!loading">
    <div class="mb-3">
      <h2>{{ room.location }}</h2>
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
              <span v-if="scheduledCourses.length">
                ({{ scheduledCourses.length === 1 ? 'One course has' : `${scheduledCourses.length} courses have` }}
                recordings scheduled in this room.)
              </span>
              <span v-if="!scheduledCourses.length">
                No course in this room has recordings scheduled.
              </span>
            </span>
            <span v-if="!room.courses.length">
              No courses are in this room.
            </span>
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <CoursesDataTable
        :courses="room.courses"
        :include-room-column="false"
        message-when-zero-courses="No courses"
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
      getRoom(id).then(room => {
        this.room = room
        this.isAuditorium = room.isAuditorium
        this.scheduledCourses = this.$_.filter(this.room.courses, 'scheduled')
        this.setPageTitle(this.room.location)
        this.$ready()
      }).catch(this.$ready)
    },
    methods: {
      onUpdateRoomCapability(capability) {
        this.room.capability = capability
      },
      tdClass(course) {
        return course.approvals.length ? 'border-bottom-zero text-no-wrap' : 'text-no-wrap'
      }
    }
  }
</script>
