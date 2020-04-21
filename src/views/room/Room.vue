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
                :room-id="room.id" />
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
      <v-data-table
        disable-pagination
        hide-default-footer
        :headers="headers"
        :items="room.courses"
      >
        <template v-slot:body="{ items }">
          <tbody v-if="items.length">
            <template v-for="course in items">
              <tr :key="course.sectionId">
                <td class="w-20" :class="tdClass(course)">
                  <router-link
                    v-if="room.capability"
                    :id="`sign-up-${course.sectionId}`"
                    class="subtitle-1"
                    :to="`/approve/${$config.currentTermId}/${course.sectionId}`">
                    <v-icon class="mb-1">mdi-video-plus</v-icon> {{ course.label }}
                  </router-link>
                  <span v-if="!room.capability">{{ course.label }}</span>
                </td>
                <td :class="tdClass(course)">{{ course.sectionId }}</td>
                <td :class="tdClass(course)">{{ course.meetingDays ? course.meetingDays.join(',') : '&mdash;' }}</td>
                <td :class="tdClass(course)">{{ course.meetingStartTime ? `${course.meetingStartTime} - ${course.meetingEndTime}` : '&mdash;' }}</td>
                <td :class="tdClass(course)">
                  {{ course.publishTypeNames || '&mdash;' }}
                </td>
                <td :class="tdClass(course)">
                  <ToggleOptOut :key="course.sectionId" :course="course" />
                </td>
              </tr>
              <tr v-if="course.approvals.length" :key="`approvals-${course.sectionId}`">
                <td colspan="5" class="pb-2">
                  <div v-if="course.approvals.length === 1">
                    "{{ course.approvals[0].recordingTypeName }}" recording was approved for "{{ course.approvals[0].publishTypeName }}" by
                    <router-link :id="`instructor-${course.approvals[0].approvedBy.uid}-mailto`" :to="`/user/${course.approvals[0].approvedBy.uid}`">
                      {{ course.approvals[0].approvedBy.name }}
                    </router-link> ({{ course.approvals[0].approvedBy.uid }}) on {{ course.approvals[0].createdAt | moment('MMM D, YYYY') }}.
                  </div>
                  <div v-if="course.approvals.length > 1">
                    <h3>Approvals</h3>
                  </div>
                </td>
                <td></td>
              </tr>
            </template>
          </tbody>
          <tbody v-if="!items.length">
            <tr>
              <td>
                No courses
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import SelectRoomCapability from '@/components/room/SelectRoomCapability'
  import ToggleOptOut from '@/components/course/ToggleOptOut'
  import Utils from '@/mixins/Utils'
  import {getRoom, setAuditorium} from '@/api/room'

  export default {
    name: 'Room',
    components: {SelectRoomCapability, ToggleOptOut},
    mixins: [Context, Utils],
    data: () => ({
      headers: [
        {text: 'Course', value: 'label'},
        {text: 'Section', value: 'sectionId'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false},
        {text: 'Publish', value: 'publishTypeNames'},
        {text: 'Opt out', value: 'hasOptedOut', sortable: false}
      ],
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
        this.setPageTitle(this.room.location)
        this.$_.each(this.room.courses, course => {
          // In support of search, we index nested course data
          course.instructorNames = this.$_.map(course.instructors, 'name')
          course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
          course.isSelectable = !course.hasOptedOut
        })
        this.scheduledCourses = this.$_.filter(this.room.courses, 'scheduled')
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
