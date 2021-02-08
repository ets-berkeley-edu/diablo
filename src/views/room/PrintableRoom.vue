<template>
  <v-app>
    <Spinner v-if="loading" />
    <v-container v-if="!loading" class="pa-10">
      <v-row>
        <v-col cols="2" md="1" class="pr-2 pt-2">
          <img alt="Oski the Bear" src="@/assets/cal-printable.png">
        </v-col>
        <v-col cols="16" md="11">
          <h1 class="pa-0 subtitle-1">Course Capture</h1>
          <h2>{{ room.location }}</h2>
        </v-col>
      </v-row>
      <v-row>
        <v-col class="pt-0">
          <v-simple-table class="mt-4">
            <template #default>
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Instructors</th>
                  <th>Days</th>
                  <th>Dates / Time</th>
                  <th>Recording</th>
                </tr>
              </thead>
              <tbody v-if="courses.length">
                <template v-for="course in courses">
                  <tr :key="course.sectionId">
                    <td :id="`course-${course.sectionId}-label`" class="font-weight-black w-20">
                      {{ course.label }}
                    </td>
                    <td>
                      <div
                        v-for="instructor in course.instructors"
                        :id="`course-${course.sectionId}-instructor-${instructor.uid}`"
                        :key="instructor.uid"
                        class="text-no-wrap"
                      >
                        {{ instructor.name }} ({{ instructor.uid }})
                      </div>
                    </td>
                    <td :id="`course-${course.sectionId}-days`" class="text-no-wrap">
                      <div v-for="(meeting, index) in course.displayMeetings" :id="`meeting-days-${index}`" :key="index">
                        {{ meeting.daysFormatted ? meeting.daysFormatted.join(', ') : '&mdash;' }}
                      </div>
                    </td>
                    <td :id="`course-${course.sectionId}-times`" class="text-no-wrap">
                      <div v-for="(meeting, index) in course.displayMeetings" :id="`meeting-times-${index}`" :key="index">
                        <div>
                          <span class="text-no-wrap">{{ meeting.startDate | moment('MMM D, YYYY') }} - </span>
                          <span class="text-no-wrap">{{ meeting.endDate | moment('MMM D, YYYY') }}</span>
                        </div>
                        <div v-if="meeting.startTimeFormatted">
                          <span class="text-no-wrap">{{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}</span>
                        </div>
                      </div>
                    </td>
                    <td :id="`course-${course.sectionId}-recording-type`" class="text-no-wrap">
                      {{ course.scheduled.recordingTypeName }}
                    </td>
                  </tr>
                </template>
              </tbody>
              <tbody v-if="!courses.length">
                <tr>
                  <td>
                    No courses
                  </td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </v-col>
      </v-row>
    </v-container>
    <v-footer fixed padless>
      <v-col class="text-center" cols="12">
        <v-icon small color="grey">mdi-copyright</v-icon> {{ new Date().getFullYear() }}
        The Regents of the University of California
      </v-col>
    </v-footer>
  </v-app>
</template>

<script>
import Context from '@/mixins/Context'
import Spinner from '@/components/util/Spinner'
import Utils from '@/mixins/Utils'
import {getRoom} from '@/api/room'

export default {
  name: 'PrintableRoom',
  components: {Spinner},
  mixins: [Context, Utils],
  data: () => ({
    courses: undefined,
    room: undefined
  }),
  created() {
    this.$loading()
    let id = this.$_.get(this.$route, 'params.id')
    getRoom(id).then(room => {
      this.room = room
      this.courses = this.$_.filter(this.room.courses, 'scheduled')
      this.$_.each(this.courses, course => {
        course.displayMeetings = this.getDisplayMeetings(course)
      })
      this.$ready(`${this.room.location} printable`)
    })
  }
}
</script>
