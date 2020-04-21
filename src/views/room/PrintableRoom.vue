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
          <div>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et
            dolore magna aliqua.
          </div>
          <v-data-table
            class="mt-4"
            disable-pagination
            hide-default-footer
            :headers="headers"
            :items="room.courses"
          >
            <template v-slot:body="{ items }">
              <tbody v-if="items.length">
                <template v-for="course in items">
                  <tr :key="course.sectionId">
                    <td class="w-20">
                      {{ course.label }}
                    </td>
                    <td>{{ course.meetingDays ? course.meetingDays.join(',') : '&mdash;' }}</td>
                    <td>{{ course.meetingStartTime ? `${course.meetingStartTime} - ${course.meetingEndTime}` : '&mdash;' }}</td>
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
      <v-row>
        <v-footer class="pt-6" color="transparent">
          <v-icon small color="grey">mdi-copyright</v-icon> {{ new Date().getFullYear() }}
          The Regents of the University of California
        </v-footer>
      </v-row>
    </v-container>
  </div>
</template>

<script>
  import Spinner from '@/components/util/Spinner'
  import Context from '@/mixins/Context'
  import {getRoom} from '@/api/room'

  export default {
    name: 'PrintableRoom',
    components: {Spinner},
    mixins: [Context],
    data: () => ({
      headers: [
        {text: 'Course', value: 'label', class: 'font-weight-black', sortable: false},
        {text: 'Days', value: 'days', class: 'font-weight-black', sortable: false},
        {text: 'Time', value: 'time', class: 'font-weight-black', sortable: false},
        {text: 'Recording', sortable: false}
      ],
      room: undefined
    }),
    created() {
      this.$loading()
      let id = this.$_.get(this.$route, 'params.id')
      getRoom(id).then(room => {
        this.room = room
        this.$ready()
      }).catch(this.$ready)
    }
  }
</script>
