<template>
  <v-app theme="light">
    <v-main class="mx-8 my-10">
      <Spinner v-if="loading" />
      <div v-if="!loading">
        <div class="d-flex">
          <img alt="Oski the Bear" class="mr-2" src="@/assets/cal-printable.png">
          <div>
            <h1 class="pa-0 text-subtitle-1">Course Capture</h1>
            <h2 class="text-h4 font-weight-bold">{{ room.location }}</h2>
          </div>
        </div>
        <table class="printable-room-courses mt-8 w-100">
          <thead>
            <tr>
              <th class="font-size-14 pa-4 text-start text-no-wrap text-medium-emphasis">Course</th>
              <th class="font-size-14 pa-4 text-start text-no-wrap text-medium-emphasis">Instructors</th>
              <th class="font-size-14 pa-4 text-start text-no-wrap text-medium-emphasis">Days</th>
              <th class="font-size-14 pa-4 text-start text-no-wrap text-medium-emphasis">Dates / Time</th>
            </tr>
          </thead>
          <tbody v-if="courses.length">
            <tr
              v-for="course in courses"
              :key="course.sectionId"
            >
              <td
                :id="`course-${course.sectionId}-label`"
                class="font-weight-black text-no-wrap px-4 py-2"
              >
                {{ course.label }}
              </td>
              <td class="px-4 py-2">
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
                class="px-4 py-2"
              >
                <div
                  v-for="(meeting, index) in course.displayMeetings"
                  :id="`meeting-days-${index}`"
                  :key="index"
                  class="text-no-wrap"
                >
                  {{ meeting.daysFormatted
                    ? meeting.daysFormatted.join(', ')
                    : '—' }}
                </div>
              </td>
              <td
                :id="`course-${course.sectionId}-times`"
                class="text-no-wrap px-4 py-2"
              >
                <div
                  v-for="(meeting, index) in course.displayMeetings"
                  :id="`meeting-times-${index}`"
                  :key="index"
                >
                  <span class="text-no-wrap">
                    {{ DateTime.fromISO(meeting.startDate).toFormat('LLL d, yyyy') }} -
                  </span>
                  <span class="text-no-wrap">
                    {{ DateTime.fromISO(meeting.endDate).toFormat('LLL d, yyyy') }}
                  </span>
                  <div v-if="meeting.startTimeFormatted" class="text-no-wrap">
                    {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td class="pa-4 text-center text-medium-emphasis" colspan="4">No courses</td>
            </tr>
          </tbody>
        </table>
      </div>
    </v-main>
    <v-footer
      v-if="!loading"
      app
      class="printable-footer"
      color="surface-light"
      height="48"
    >
      <div class="text-center w-100">
        <v-icon class="mb-1" :icon="mdiCopyright" size="x-small" />
        <span class="sr-only">copyright</span>
        {{ DateTime.now().year }} The Regents of the University of California
      </div>
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
import {getDisplayMeetings} from '@/lib/berkeley'
import {getRoom} from '@/api/room'
import {useContextStore} from '@/stores/context'
import Spinner from '@/components/util/Spinner'

const contextStore = useContextStore()
const courses = ref([])
const {loading} = storeToRefs(contextStore)
const room = ref({})
const route = useRoute()

contextStore.loadingStart()

onMounted(() => {
  const id = get(route, 'params.id')
  getRoom(id).then(roomData => {
    room.value = roomData
    courses.value = filter(roomData.courses, 'scheduled')
    each(courses.value, course => {
      course.displayMeetings = getDisplayMeetings(course)
    })
    contextStore.loadingComplete(`${roomData.location} Printable`)
  })
})
</script>

<style scoped>
.printable-footer {
  max-height: 48px !important;
}
.printable-room-courses {
  border-collapse: collapse;
}
.printable-room-courses th {
  width: min-content;
}
</style>
