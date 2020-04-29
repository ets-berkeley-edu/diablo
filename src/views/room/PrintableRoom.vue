<template>
  <div>
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
          <v-data-table
            class="mt-4"
            disable-pagination
            disable-sort
            hide-default-footer
            :headers="headers"
            :items="scheduledCourses"
          >
            <template v-slot:body="{ items }">
              <tbody v-if="items.length">
                <template v-for="course in items">
                  <tr :key="course.sectionId">
                    <td class="font-weight-black text-no-wrap w-30">
                      {{ course.label }}
                    </td>
                    <td>
                      <div v-for="instructor in course.instructors" :key="instructor.uid">
                        {{ instructor.name }} ({{ instructor.uid }})
                      </div>
                    </td>
                    <td class="text-no-wrap">{{ course.meetingDays ? course.meetingDays.join(',') : '&mdash;' }}</td>
                    <td class="text-no-wrap">{{ course.meetingStartTime ? `${course.meetingStartTime} - ${course.meetingEndTime}` : '&mdash;' }}</td>
                    <td>
                      <div v-if="course.scheduled">
                        {{ course.scheduled.recordingTypeName }}
                      </div>
                      <div v-if="!course.scheduled">
                        &mdash;
                      </div>
                    </td>
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
        </v-col>
      </v-row>
      <v-row no-gutters>
        <v-col class="pt-12">
          <v-footer color="transparent">
            <v-icon small color="grey">mdi-copyright</v-icon> {{ new Date().getFullYear() }}
            The Regents of the University of California
          </v-footer>
        </v-col>
      </v-row>
    </v-container>
  </div>
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
      headers: [
        {text: 'Course'},
        {text: 'Instructors'},
        {text: 'Days'},
        {text: 'Time'},
        {text: 'Recording'}
      ],
      room: undefined,
      scheduledCourses: undefined
    }),
    created() {
      this.$loading()
      let id = this.$_.get(this.$route, 'params.id')
      getRoom(id).then(room => {
        this.room = room
        this.scheduledCourses = this.$_.filter(this.room.courses, 'scheduled')
        this.setPageTitle(this.room.location)
        this.$ready()
      }).catch(this.$ready)
    }
  }
</script>
