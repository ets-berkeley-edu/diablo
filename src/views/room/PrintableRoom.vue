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
            <template v-slot:default>
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Instructors</th>
                  <th>Days</th>
                  <th>Time</th>
                  <th>Recording</th>
                </tr>
              </thead>
              <tbody v-if="courses.length">
                <template v-for="course in courses">
                  <tr :key="course.sectionId">
                    <td :id="`course-${course.sectionId}-label`" class="font-weight-black text-no-wrap w-30">
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
                      {{ course.meetingDays ? course.meetingDays.join(',') : '&mdash;' }}
                    </td>
                    <td :id="`course-${course.sectionId}-times`" class="text-no-wrap">
                      {{ course.meetingStartTime ? `${course.meetingStartTime} - ${course.meetingEndTime}` : '&mdash;' }}
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
        this.$ready(`${this.room.location} printable`)
      }).catch(this.$ready)
    }
  }
</script>
