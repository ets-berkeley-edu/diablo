<template>
  <v-container fluid>
    <v-row no-gutters>
      <v-card flat>
        <router-link
          :id="`link-course-${course.sectionId}`"
          :to="`/course/${$config.currentTermId}/${course.sectionId}`"
        >
          <h2>{{ course.label }}</h2>
        </router-link>
        <div class="pt-2">
          <h3 id="course-title">{{ course.courseTitle }}</h3>
          Section ID: {{ course.sectionId }}
        </div>
      </v-card>
    </v-row>
    <v-row>
      <v-col>
        <v-card outlined tile>
          <v-card-title>
            <h4>Scheduled on {{ course.scheduled.createdAt | moment('MMM D, YYYY') }}</h4>
          </v-card-title>
          <v-card-subtitle>
            {{ summary }}
          </v-card-subtitle>
          <v-card-text>
            <div v-if="course.scheduled.hasObsoleteInstructors">
              <h5>Obsolete Instructors</h5>
              <div v-for="instructor in course.scheduled.instructors" :key="instructor.uid">
                <Instructor :course="course" :instructor="instructor" />
              </div>
            </div>
            <div :class="{'pt-2': course.scheduled.hasObsoleteInstructors}">
              <h5>Meeting</h5>
              <div>
                <CourseRoom :course="course" :room="course.scheduled.room" />
              </div>
              <div v-if="!isRoomObsolete && (course.scheduled.hasObsoleteDates || course.scheduled.hasObsoleteTimes)">
                <div class="d-flex pt-2">
                  <v-tooltip
                    v-if="course.scheduled.hasObsoleteDates"
                    :id="`tooltip-course-${course.sectionId}-obsolete-dates`"
                    bottom
                  >
                    <template v-slot:activator="{ on }">
                      <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-calendar-export</v-icon>
                    </template>
                    Meeting dates have changed.
                  </v-tooltip>
                  <div>
                    {{ course.scheduled.meetingStartDate }} to {{ course.scheduled.meetingEndDate }}
                  </div>
                </div>
                <div class="d-flex pt-2">
                  <v-tooltip
                    v-if="course.scheduled.hasObsoleteTimes"
                    :id="`tooltip-course-${course.sectionId}-obsolete-times`"
                    bottom
                  >
                    <template v-slot:activator="{ on }">
                      <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-clock-alert-outline</v-icon>
                    </template>
                    Meeting times have changed.
                  </v-tooltip>
                  <div>
                    {{ $_.join(course.scheduled.meetingDays, ' ') }},
                    {{ course.scheduled.meetingStartTimeFormatted }} - {{ course.scheduled.meetingEndTimeFormatted }}
                  </div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col>
        <v-card outlined tile>
          <v-card-title>
            <h4>Current</h4>
          </v-card-title>
          <v-card-subtitle v-if="sisDataImportDate">
            SIS Data last imported on {{ sisDataImportDate.finishedAt | moment('MMM D, YYYY') }}.
          </v-card-subtitle>
          <v-card-text>
            <div v-if="course.scheduled.hasObsoleteInstructors">
              <h5>Instructors</h5>
              <div v-for="instructor in course.instructors" :key="instructor.uid">
                <Instructor :course="course" :instructor="instructor" />
              </div>
            </div>
            <div :class="{'pt-2': course.scheduled.hasObsoleteInstructors}">
              <h5>All Meetings</h5>
              <div v-for="meeting in meetings" :key="meeting.location">
                <CourseRoom :course="course" :room="meeting.room" />
                <div v-if="!isRoomObsolete && (course.scheduled.hasObsoleteDates || course.scheduled.hasObsoleteTimes)" class="pb-2">
                  <div class="d-flex">
                    <div>
                      {{ meeting.startDate }} to {{ meeting.endDate }}
                    </div>
                  </div>
                  <div class="d-flex">
                    <div>
                      {{ $_.join(meeting.daysFormatted, ' ') }},
                      {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import CourseRoom from '@/components/course/CourseRoom'
  import Instructor from '@/components/course/Instructor'
  import Utils from '@/mixins/Utils'
  import {getLastSuccessfulRun} from '@/api/job'

  export default {
    name: 'ObsoleteSchedule',
    mixins: [Utils],
    components: {Instructor, CourseRoom},
    props: {
      course: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      meetings: undefined,
      isRoomObsolete: undefined,
      sisDataImportDate: undefined,
      summary: undefined
    }),
    created() {
      const hasObsoleteRoom = this.course.scheduled.hasObsoleteRoom
      let considerations = {
        instructors: this.course.scheduled.hasObsoleteInstructors,
        room: hasObsoleteRoom
      }
      if (!hasObsoleteRoom) {
        considerations = {...considerations, ...{
          dates: this.course.scheduled.hasObsoleteDates,
          times: this.course.scheduled.hasObsoleteTimes
        }}
      }
      const obsoleteItems = this.$_.keys(this.$_.pickBy(considerations))
      this.summary = this.$_.capitalize(`${this.oxfordJoin(obsoleteItems)} ${hasObsoleteRoom && obsoleteItems.length === 1 ? 'is' : 'are'} obsolete.`)
      this.meetings = this.course.meetings.eligible.concat(this.course.meetings.ineligible)
      this.isRoomObsolete = !this.isInRoom(this.course, this.course.scheduled.room)
      getLastSuccessfulRun('sis_data_refresh').then(data => {
        this.sisDataImportDate = data
      })
    }
  }
</script>
