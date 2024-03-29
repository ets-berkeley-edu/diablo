<template>
  <v-container fluid>
    <v-row no-gutters>
      <v-card flat>
        <router-link
          :id="`link-course-${course.sectionId}`"
          :to="`/course/${$config.currentTermId}/${course.sectionId}`"
        >
          <h2 :class="{'line-through': course.deletedAt}">{{ course.label }}</h2>
        </router-link>
        <div class="pr-2">
          <h3 id="course-title" :class="{'line-through': course.deletedAt}">{{ course.courseTitle }}</h3>
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
            <div v-if="instructorsNew.length && !course.deletedAt">
              <h5>Joined course <i>after</i> recordings were scheduled</h5>
              <div v-for="instructor in instructorsNew" :key="instructor.uid">
                <Instructor
                  :id="`course-${course.sectionId}-instructor-${instructor.uid}-new`"
                  :course="course"
                  :instructor="instructor"
                />
              </div>
            </div>
            <div v-if="course.deletedAt" class="pb-2">
              <a
                id="link-to-edit-kaltura-event"
                :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${course.scheduled.kalturaScheduleId}`"
                target="_blank"
                aria-label="Open Kaltura MediaSpace in a new window"
              >
                Kaltura series {{ course.scheduled.kalturaScheduleId }} <v-icon small class="pb-1">mdi-open-in-new</v-icon>
              </a>
            </div>
            <div v-if="instructorsObsolete.length && !course.deletedAt" :class="{'pt-2': instructorsNew.length}">
              <h5>Obsolete Instructors</h5>
              <div v-for="instructor in instructorsObsolete" :key="instructor.uid">
                <Instructor
                  :id="`course-${course.sectionId}-instructor-${instructor.uid}-obsolete`"
                  :course="course"
                  :instructor="instructor"
                />
              </div>
            </div>
            <div
              v-if="(isRoomObsolete || course.scheduled.hasObsoleteDates || course.scheduled.hasObsoleteTimes) && !course.deletedAt"
              :class="{'pt-2': course.scheduled.hasObsoleteInstructors}"
            >
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
                    <template>
                      <v-icon class="pr-1" color="yellow darken-2">mdi-calendar-export</v-icon>
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
                    <template>
                      <v-icon class="pr-1" color="yellow darken-2">mdi-clock-alert-outline</v-icon>
                    </template>
                    Meeting times have changed.
                  </v-tooltip>
                  <div>
                    <Days :names-of-days="course.scheduled.meetingDaysNames" :omit-comma="true" />,
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
            <div v-if="course.deletedAt">
              <v-icon color="red" class="font-weight-bold pb-1 pl-0">mdi-close</v-icon>
              <span class="font-weight-bold red--text">UC Berkeley has canceled this section.</span>
            </div>
            <div v-if="course.scheduled.hasObsoleteInstructors && !course.deletedAt">
              <h5>Instructors</h5>
              <div v-if="course.instructors.length">
                <div v-for="instructor in course.instructors" :key="instructor.uid">
                  <Instructor :course="course" :instructor="instructor" />
                </div>
              </div>
              <div v-if="!course.instructors.length">
                None
              </div>
            </div>
            <div
              v-if="(isRoomObsolete || course.scheduled.hasObsoleteDates || course.scheduled.hasObsoleteTimes) && !course.deletedAt"
              :class="{'pt-2': course.scheduled.hasObsoleteInstructors}"
            >
              <h5 v-if="this.$_.some(meetings, m => !!m.room)">All Meetings</h5>
              <h5 v-if="!this.$_.some(meetings, m => !!m.room)">{{ course.label }} currently has no meeting locations.</h5>
              <div v-for="(meeting, index) in meetings" :key="index">
                <CourseRoom :course="course" :room="meeting.room" />
                <div v-if="!isRoomObsolete && (course.scheduled.hasObsoleteDates || course.scheduled.hasObsoleteTimes)" class="pb-2">
                  <div class="d-flex">
                    <div v-if="meeting.eligible">
                      {{ meeting.recordingStartDate }} to {{ meeting.recordingEndDate }}
                    </div>
                    <div v-if="!meeting.eligible">
                      {{ meeting.startDate }} to {{ meeting.endDate }}
                    </div>
                  </div>
                  <div class="d-flex">
                    <div>
                      <Days :names-of-days="meeting.daysNames" :omit-comma="true" />,
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
import Days from '@/components/util/Days'
import Instructor from '@/components/course/Instructor'
import Utils from '@/mixins/Utils'
import {getCalnetUser} from '@/api/user'
import {getLastSuccessfulRun} from '@/api/job'

export default {
  name: 'ObsoleteSchedule',
  mixins: [Utils],
  components: {CourseRoom, Days, Instructor},
  props: {
    course: {
      required: true,
      type: Object
    }
  },
  data: () => ({
    instructorsNew: [],
    instructorsObsolete: [],
    isRoomObsolete: undefined,
    meetings: undefined,
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
    if (!this.course.deletedAt) {
      const obsoleteItems = this.$_.keys(this.$_.pickBy(considerations))
      this.summary = this.$_.capitalize(`${this.oxfordJoin(obsoleteItems)} ${hasObsoleteRoom && obsoleteItems.length === 1 ? 'is' : 'are'} obsolete.`)
      this.meetings = this.course.meetings.eligible.concat(this.course.meetings.ineligible)
      this.isRoomObsolete = !this.isInRoom(this.course, this.course.scheduled.room)
    }
    getLastSuccessfulRun('sis_data_refresh').then(data => {
      this.sisDataImportDate = data
    })
    if (this.course.scheduled.hasObsoleteInstructors) {
      const courseUids = this.$_.map(this.course.instructors, 'uid')
      const scheduledUids = this.course.scheduled.instructorUids
      this.addUsers(this.instructorsNew, courseUids.filter(uid => !scheduledUids.includes(uid)))
      this.addUsers(this.instructorsObsolete, scheduledUids.filter(uid => !courseUids.includes(uid)))
    }
  },
  methods: {
    addUsers(list, uids) {
      this.$_.each(uids, uid => {
        this.fetchUser(uid).then(user => list.push(user))
      })
    },
    fetchUser(uid) {
      return new Promise(resolve => {
        this.$_.each(this.course.instructors, instructor => {
          if (instructor.uid === uid) {
            resolve(instructor)
          }
        })
        getCalnetUser(uid).then(user => {
          resolve(user)
        })
      })
    }
  }
}
</script>
