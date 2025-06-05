<template>
  <v-app class="d-flex flex-column fill-height">
    <Spinner v-if="loading" />

    <v-main v-else class="flex-grow-1">
      <v-container class="pa-10">
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
            <table
              class="v-simple-table mt-4"
              style="width: 100%; border-collapse: collapse;"
            >
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
                <tr
                  v-for="course in courses"
                  :key="course.sectionId"
                  style="border-bottom: 1px solid rgba(0, 0, 0, 0.12);"
                >
                  <td
                    :id="`course-${course.sectionId}-label`"
                    class="font-weight-black w-20"
                  >
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

                  <td
                    :id="`course-${course.sectionId}-days`"
                    class="text-no-wrap"
                  >
                    <div
                      v-for="(meeting, index) in course.displayMeetings"
                      :id="`meeting-days-${index}`"
                      :key="index"
                    >
                      {{ meeting.daysFormatted
                        ? meeting.daysFormatted.join(', ')
                        : '—' }}
                    </div>
                  </td>

                  <td
                    :id="`course-${course.sectionId}-times`"
                    class="text-no-wrap"
                  >
                    <div
                      v-for="(meeting, index) in course.displayMeetings"
                      :id="`meeting-times-${index}`"
                      :key="index"
                    >
                      <div>
                        <span class="text-no-wrap">
                          {{ DateTime.fromISO(meeting.startDate).toFormat('LLL d, yyyy') }} -
                        </span>
                        <span class="text-no-wrap">
                          {{ DateTime.fromISO(meeting.endDate).toFormat('LLL d, yyyy') }}
                        </span>
                      </div>
                      <div v-if="meeting.startTimeFormatted">
                        <span class="text-no-wrap">
                          {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td
                    :id="`course-${course.sectionId}-recording-type`"
                    class="text-no-wrap"
                  >
                    {{ get(course, 'scheduled[0].recordingTypeName') }}
                  </td>
                </tr>
              </tbody>

              <tbody v-else>
                <tr>
                  <td colspan="5">No courses</td>
                </tr>
              </tbody>
            </table>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <v-footer padless>
      <v-col class="text-center" cols="12">
        <v-icon size="small" :icon="mdiCopyright" />
        <span class="sr-only">copyright</span>
        {{ DateTime.now().year }} The Regents of the University of California
      </v-col>
    </v-footer>
  </v-app>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {DateTime} from 'luxon'
import {each, filter, get} from 'lodash'
import {mdiCopyright} from '@mdi/js'
import {useContextStore} from '@/stores/context'
import {getDisplayMeetings} from '@/lib/utils'
import {getRoom} from '@/api/room'
import Spinner from '@/components/util/Spinner'

// Pinia store for global loading/ready
const contextStore = useContextStore()
const {loading} = storeToRefs(contextStore)

// Vue Router
const route = useRoute()

// Local reactive state
const room = ref({})
const courses = ref([])

onMounted(() => {
  contextStore.loadingStart()
  const id = get(route, 'params.id')

  getRoom(id).then(roomData => {
    room.value = roomData
    courses.value = filter(roomData.courses, 'scheduled')
    each(courses.value, course => {
      course.displayMeetings = getDisplayMeetings(course)
    })
    contextStore.loadingComplete(`${roomData.location} printable`)
  })
})
</script>

<style>
.fill-height {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

v-app > v-footer {
  margin-top: auto;
}

table.v-simple-table th,
table.v-simple-table td {
  padding: 12px 8px;
}
</style>
