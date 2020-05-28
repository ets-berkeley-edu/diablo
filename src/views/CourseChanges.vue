<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <h1><v-icon class="pb-3" large>mdi-swap-horizontal</v-icon> Course Changes</h1>
      </div>
    </v-card-title>
    <v-data-table
      disable-pagination
      :headers="headers"
      hide-default-footer
      item-key="sectionId"
      :items="courses"
    >
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-if="!items.length">
            <td colspan="10">
              <div class="ma-4 text-no-wrap title">
                No changes for courses invited to Course Capture.
              </div>
            </td>
          </tr>
          <tr v-for="course in items" :key="course.sectionId">
            <td class="pa-3 text-no-wrap">
              <div class="font-weight-black">
                {{ course.label }}
                <v-tooltip v-if="course.wasApprovedByAdmin" bottom nudge-right="200px">
                  <template v-slot:activator="{ on }">
                    <v-icon
                      color="green"
                      class="pa-0"
                      dark
                      v-on="on"
                    >
                      mdi-account-check-outline
                    </v-icon>
                  </template>
                  Course Capture Admin {{ $_.last(course.approvals).approvedBy.name }}
                  submitted approval on
                  {{ $_.last(course.approvals).createdAt | moment('MMM D, YYYY') }}.
                </v-tooltip>
              </div>
              <div>
                {{ course.sectionId }}
              </div>
              <div v-if="course.scheduled.hasObsoleteMeetingTimes">
                <div>
                  {{ course.scheduled.meetingDays.join(',') }} {{ course.scheduled.meetingStartTime }} - {{ course.scheduled.meetingEndTime }}
                </div>
                <div class="primary--text">
                  <v-icon small color="primary">mdi-arrow-down-bold</v-icon>
                  changed to
                </div>           
              </div>
              <div>
                {{ course.meetingDays.join(',') }} {{ course.meetingStartTime }} - {{ course.meetingEndTime }}
              </div>
              <div>
                {{ course.publishTypeNames }}
              </div>
            </td>
            <td class="text-no-wrap">
              <div v-for="roomBefore in course.roomsBefore" :key="roomBefore.id">
                <div>
                  <router-link
                    :id="`course-${course.sectionId}-room-before-${roomBefore.id}`"
                    :to="`/room/${roomBefore.id}`"
                  >
                    {{ roomBefore.location }}
                  </router-link>
                </div>
                <div class="primary--text">
                  <v-icon small color="primary">mdi-arrow-down-bold</v-icon>
                  changed to
                </div>
              </div>
              <router-link
                v-if="course.room"
                :id="`course-${course.sectionId}-room-${course.room.id}`"
                :to="`/room/${course.room.id}`"
              >
                {{ course.room.location }}
              </router-link>
              <span v-if="!course.room">&mdash;</span>
            </td>
            <td>
              <div v-if="course.scheduled.hasObsoleteInstructors">
                <div v-for="instructor in course.scheduled.instructors" :key="instructor.uid">
                  <router-link :id="`instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                    {{ instructor.name }}
                  </router-link> ({{ instructor.uid }})
                </div>
              </div>
              <div class="primary--text">
                <v-icon small color="primary">mdi-arrow-down-bold</v-icon>
                changed to
              </div>
              <div v-for="instructor in course.instructors" :key="instructor.uid">
                <v-tooltip v-if="!instructor.wasSentInvite" bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon
                      color="yellow darken-2"
                      class="pb-1 pl-1"
                      dark
                      v-on="on"
                    >
                      mdi-alert-circle-outline
                    </v-icon>
                  </template>
                  <div>
                    No invite sent to {{ instructor.name }}.
                  </div>
                </v-tooltip>
                <router-link :id="`instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                  {{ instructor.name }}
                </router-link> ({{ instructor.uid }})
              </div>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
  import Context from '@/mixins/Context'
  import {getCourseChanges} from '@/api/course'

  export default {
    name: 'CourseChanges',
    mixins: [Context],
    data: () => ({
      courses: undefined,
      headers: [
        {text: 'Course Information', value: 'label'},
        {text: 'Room', value: 'meetingLocation'},
        {text: 'Instructor(s)', value: 'instructorNames', sortable: false}
      ]
    }),
    created() {
      this.$loading()
      getCourseChanges(this.$config.currentTermId).then(data => {
        this.courses = []
        this.$_.each(data, course => {
          course.roomsBefore = []
          this.$_.each([course.approvals, course.scheduled], actions => {
            this.$_.each(this.$_.filter(actions, 'hasObsoleteRoom'), obsolete => {
              if (!this.$_.includes(course.roomsBefore, obsolete.room)) {
                course.roomsBefore.push(obsolete.room)
              }
            })
          })
          this.courses.push(course)
        })
        if (this.courses.length < 2) {
          this.$_.each(this.headers, h => {
            h.sortable = false
          })
        }
        this.$ready()
      })
    }
  }
</script>
