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
                No changes within scheduled courses.
              </div>
            </td>
          </tr>
          <tr v-for="course in items" :key="course.sectionId">
            <td class="pa-3 text-no-wrap">
              <div class="font-weight-black">
                <router-link
                  :id="`link-course-${course.sectionId}`"
                  :to="`/course/${$config.currentTermId}/${course.sectionId}`"
                >
                  {{ course.label }}
                </router-link>
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
              <div v-if="course.scheduled.hasObsoleteTimes" :id="`course-${course.sectionId}-obsolete-meeting-times`">
                <div :id="`course-${course.sectionId}-meeting-times-old`">
                  {{ course.scheduled.meetingDays.join(',') }} {{ course.scheduled.meetingStartTime }} - {{ course.scheduled.meetingEndTime }}
                </div>
                <div class="primary--text">
                  <v-icon small color="primary">mdi-arrow-down-bold</v-icon>
                  changed to
                </div>
              </div>
              <div v-for="(meeting, index) in course.meetings.eligible" :id="`course-${course.sectionId}-meeting-times-eligible-${index}`" :key="index">
                {{ meeting.daysFormatted.join(',') }} {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }} (Eligible)
              </div>
              <div v-for="(meeting, index) in course.meetings.ineligible" :id="`course-${course.sectionId}-meeting-times-ineligible-${index}`" :key="index">
                {{ meeting.daysFormatted.join(',') }} {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }} (Ineligible)
              </div>
              <div v-if="course.scheduled.hasObsoleteDates" :id="`course-${course.sectionId}-obsolete-meeting-dates`">
                <div :id="`course-${course.sectionId}-meeting-dates-old`">
                  {{ course.scheduled.meetingStartDate }} - {{ course.scheduled.meetingEndDate }}
                </div>
                <div class="primary--text">
                  <v-icon small color="primary">mdi-arrow-down-bold</v-icon>
                  changed to
                </div>
                <div v-for="(meeting, index) in course.meetings.eligible" :id="`course-${course.sectionId}-meeting-dates-eligible-${index}`" :key="index">
                  {{ meeting.recordingStartDate }} - {{ meeting.recordingEndDate }} (Eligible)
                </div>
                <div v-for="(meeting, index) in course.meetings.ineligible" :id="`course-${course.sectionId}-meeting-dates-ineligible-${index}`" :key="index">
                  {{ meeting.startDate }} - {{ meeting.endDate }} (Ineligible)
                </div>
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
              <div v-for="(meeting, index) in course.meetings.eligible" :key="index">
                <router-link
                  :id="`course-${course.sectionId}-room-new-eligible-${meeting.room.id}-${index}`"
                  :to="`/room/${meeting.room.id}`"
                >
                  {{ meeting.room.location }} (Eligible)
                </router-link>
              </div>
              <div v-for="(meeting, index) in course.meetings.ineligible" :key="index">
                <router-link
                  v-if="meeting.room"
                  :id="`course-${course.sectionId}-room-new-ineligible-${meeting.room.id}-${index}`"
                  :to="`/room/${meeting.room.id}`"
                >
                  {{ meeting.room.location }} (Ineligible)
                </router-link>
                <span v-if="!meeting.room">&mdash;</span>
              </div>
            </td>
            <td>
              <div v-if="course.scheduled.hasObsoleteInstructors">
                <div v-for="instructor in course.scheduled.instructors" :key="instructor.uid">
                  <v-tooltip v-if="instructor.approval" :id="`tooltip-approval-${course.sectionId}-by-${instructor.uid}`" bottom>
                    <template v-slot:activator="{ on }">
                      <v-icon
                        :color="instructor.approval ? 'green' : 'yellow darken-2'"
                        class="pa-0"
                        dark
                        v-on="on"
                      >
                        mdi-check
                      </v-icon>
                    </template>
                    Approval submitted on {{ instructor.approval.createdAt | moment('MMM D, YYYY') }}.
                  </v-tooltip>
                  <router-link :id="`instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                    {{ instructor.name }}
                  </router-link> ({{ instructor.uid }})
                </div>
                <div class="primary--text">
                  <v-icon small color="primary">mdi-arrow-down-bold</v-icon>
                  changed to
                </div>
              </div>
              <div v-for="instructor in course.instructors" :key="instructor.uid">
                <v-tooltip v-if="instructor.approval" :id="`tooltip-approval-${course.sectionId}-by-${instructor.uid}`" bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon
                      :color="instructor.approval ? 'green' : 'yellow darken-2'"
                      class="pa-0"
                      dark
                      v-on="on"
                    >
                      mdi-check
                    </v-icon>
                  </template>
                  Approval submitted on {{ instructor.approval.createdAt | moment('MMM D, YYYY') }}.
                </v-tooltip>
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
        {text: 'Room', sortable: false},
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
        this.$ready('Course Changes')
      })
    }
  }
</script>
