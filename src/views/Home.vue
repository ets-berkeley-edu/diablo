<template>
  <v-card
    v-if="!contextStore.loading"
    class="border-sm"
  >
    <v-card-title>
      <PageTitle
        :icon="mdiVideoPlus"
        :text="`Your ${config.currentTermName} ${pluralize('Course', size(currentUser.courses), {includeCount: false})}`"
      />
    </v-card-title>
    <v-card-text>
      <v-container class="ml-8 mb-6">
        <v-row class="px-6 py-2">
          <ToggleOptOut
            :term-id="`${config.currentTermId}`"
            section-id="all"
            :instructor-uid="currentUser.uid"
            :initial-value="currentUser.hasOptedOutForTerm"
            :disabled="currentUser.hasOptedOutForAllTerms"
            label="for current semester"
            :before-toggle="() => refreshingCourses = true"
            :on-toggle="reloadCoursesTable"
          />
        </v-row>
        <v-row class="px-6 py-2">
          <ToggleOptOut
            term-id="all"
            section-id="all"
            :instructor-uid="currentUser.uid"
            :initial-value="currentUser.hasOptedOutForAllTerms"
            label="for all semesters"
            :before-toggle="() => refreshingCourses = true"
            :on-toggle="reloadCoursesTable"
          />
        </v-row>
      </v-container>
      <Spinner v-if="refreshingCourses" />
      <template v-if="!refreshingCourses">
        <v-row v-for="(courses, index) in [eligibleCourses, ineligibleCourses]" :key="index" class="py-5">
          <h2 class="pa-4 text-medium-emphasis w-100">
            {{ index === 0 ? 'Courses eligible for capture' : 'Courses not in a course capture classroom' }}
          </h2>
          <div class="overflow-x-auto px-md-4 w-100">
            <div v-if="isEmpty(courses)" class="px-4 pt-2">No courses.</div>
            <v-data-table
              v-if="size(courses)"
              :id="getTableId(index)"
              class="instructor-courses overflow-y-visible"
              disable-sort
              :headers="index === 0 ? eligibleHeaders : ineligibleHeaders"
              :hide-default-footer="true"
              :items="courses"
              :items-per-page="100"
            >
              <template #headers="{columns}">
                <tr>
                  <th
                    v-for="(column, colIndex) in columns"
                    :id="`${getTableId(index)}-${column.value}-th`"
                    :key="colIndex"
                    class="text-start text-no-wrap"
                    scope="col"
                  >
                    <span class="font-size-12 font-weight-bold">{{ column.title }}</span>
                  </th>
                </tr>
              </template>
              <template #body="{items}">
                <!-- eslint-disable-next-line vue/no-v-for-template-key -->
                <template v-for="(course, courseIndex) in items" :key="course.sectionId">
                  <tr :id="`${getTableId(index)}-${course.sectionId}`">
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-label`"
                      :aria-rowspan="size(course.displayMeetings)"
                      class="text-no-wrap"
                      :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-bottom-zero': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-label-th`"
                    >
                      <div v-for="(courseCode, courseCodeIndex) in course.courseCodes" :key="courseCode">
                        <router-link
                          v-if="courseCodeIndex === 0"
                          :id="`link-course-${course.sectionId}`"
                          :to="`/course/${config.currentTermId}/${course.sectionId}`"
                        >
                          {{ courseCode }}
                        </router-link>
                        <span v-if="courseCodeIndex > 0">{{ courseCode }}</span>
                      </div>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-title`"
                      :aria-rowspan="size(course.displayMeetings)"
                      :class="{'border-bottom-zero': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-title-th`"
                    >
                      <span aria-hidden="true">{{ course.courseTitle || '&mdash;' }}</span>
                      <span class="sr-only">{{ course.courseTitle || 'blank' }}</span>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-instructors`"
                      :aria-rowspan="size(course.displayMeetings)"
                      :class="{'border-bottom-zero': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-instructors-th`"
                    >
                      {{ oxfordJoin(map(course.instructors, 'name')) }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-room-0`"
                      :class="{'border-bottom-zero': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-room-th`"
                    >
                      {{ course.displayMeetings[0].room.location }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-days-0`"
                      :class="{'border-bottom-zero': size(course.displayMeetings) > 1}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-days-th`"
                    >
                      <Days v-if="size(course.displayMeetings[0].daysNames)" :names-of-days="course.displayMeetings[0].daysNames" />
                      <span v-if="isEmpty(course.displayMeetings[0].daysNames)">&mdash;</span>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-time-0`"
                      :class="{'border-bottom-zero': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-time-th`"
                    >
                      <div v-if="course.nonstandardMeetingDates" class="pt-2">
                        <span class="text-no-wrap">
                          {{
                            DateTime
                              .fromISO(course.displayMeetings[0].startDate)
                              .toFormat('MMM d, yyyy')
                          }} -
                        </span>
                        <span class="text-no-wrap">
                          {{
                            DateTime
                              .fromISO(course.displayMeetings[0].endDate)
                              .toFormat('MMM d, yyyy')
                          }}
                        </span>
                      </div>
                      <span aria-hidden="true" class="text-no-wrap">{{ course.displayMeetings[0].startTimeFormatted }} - {{ course.displayMeetings[0].endTimeFormatted }}</span>
                      <span class="sr-only">{{ course.displayMeetings[0].startTimeFormatted }} to {{ course.displayMeetings[0].endTimeFormatted }}</span>
                    </td>
                    <td
                      v-if="index === 0"
                      :id="`${getTableId(index)}-${course.sectionId}-hasOptedOut`"
                      :aria-rowspan="size(course.displayMeetings)"
                      :class="{'border-0': size(course.displayMeetings) && courseIndex === (size(courses) - 1)}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-hasOptedOut-th`"
                    >
                      <ToggleOptOut
                        :aria-label="`Opt out course ${get(course.courseCodes, '0', course.title)}.`"
                        :disabled="course.hasBlanketOptedOut"
                        :initial-value="course.hasOptedOut"
                        :instructor-uid="currentUser.uid"
                        :section-id="`${course.sectionId}`"
                        :term-id="`${course.termId}`"
                      />
                    </td>
                  </tr>
                  <tr v-for="(meeting, meetingIndex) in tail(course.displayMeetings)" :id="`${getTableId(index)}-${course.sectionId}-${meetingIndex}`" :key="`${course.sectionId}-${meetingIndex}`">
                    <td :aria-hidden="true" colspan="3"></td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-room-${meetingIndex + 1}`"
                      class="pt-0 text-no-wrap"
                      :columnheader="`${getTableId(index)}-room-th`"
                    >
                      {{ meeting.room.location }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-days-${meetingIndex + 1}`"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-days-th`"
                    >
                      <Days :names-of-days="meeting.daysNames" />
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-time-${meetingIndex + 1}`"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-time-th`"
                    >
                      <div v-if="course.nonstandardMeetingDates" class="pt-2">
                        <span class="text-no-wrap">
                          {{
                            DateTime
                              .fromISO(meeting.startDate)
                              .toFormat('MMM d, yyyy')
                          }} -
                        </span>
                        <span class="text-no-wrap">
                          {{
                            DateTime
                              .fromISO(meeting.endDate)
                              .toFormat('MMM d, yyyy')
                          }}
                        </span>
                      </div>
                      <div :class="{'pb-2': course.nonstandardMeetingDates && meetingIndex === (size(course.displayMeetings) - 1)}">
                        {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
                      </div>
                    </td>
                    <td v-if="index === 0" :aria-hidden="true"></td>
                  </tr>
                </template>
              </template>
            </v-data-table>
          </div>
        </v-row>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup>
import {DateTime} from 'luxon'
import {each, get, isEmpty, map, size, tail} from 'lodash'
import {mdiVideoPlus} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import {alertScreenReader, getCourseCodes, getDisplayMeetings, oxfordJoin, partitionCoursesByEligibility, pluralize} from '@/lib/utils'
import Days from '@/components/util/Days'
import {getCurrentUser} from '@/api/auth'
import PageTitle from '@/components/util/PageTitle'
import Spinner from '@/components/util/Spinner'
import ToggleOptOut from '@/components/course/ToggleOptOut'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const {config, currentUser} = storeToRefs(contextStore)
const eligibleCourses = ref([])
const ineligibleCourses = ref([])
const ineligibleHeaders = [
  {title: 'Course', value: 'label'},
  {title: 'Title', value: 'title'},
  {title: 'Instructors', value: 'instructors'},
  {title: 'Room', value: 'room'},
  {title: 'Days', value: 'days'},
  {title: 'Time', value: 'time'},
]
const eligibleHeaders = [
  ...ineligibleHeaders,
  {title: 'Opt out', value: 'hasOptedOut'}
]
const refreshingCourses = ref(false)

onMounted(() => {
  contextStore.loadingStart()
  refreshCourses()
  contextStore.loadingComplete()
})

const getTableId = index => {
  return index === 0 ? 'courses-table-eligible' : 'courses-table-ineligible'
}

const refreshCourses = () => {
  each(currentUser.value.courses, course => {
    course.courseCodes = getCourseCodes(course)
  })
  eligibleCourses.value = []
  ineligibleCourses.value = []
  partitionCoursesByEligibility(currentUser.value.courses, eligibleCourses.value, ineligibleCourses.value)
  each([...eligibleCourses.value, ...ineligibleCourses.value], course => {
    course.displayMeetings = getDisplayMeetings(course)
  })
}

const reloadCoursesTable = (srAlert = '') => {
  getCurrentUser().then(user => {
    contextStore.setCurrentUser(user)
    refreshCourses()
    refreshingCourses.value = false
    alertScreenReader(`${srAlert}. Courses table refreshed.`)
  })
}
</script>

<style>
.instructor-courses .v-table__wrapper {
  overflow: visible !important;
}
</style>
