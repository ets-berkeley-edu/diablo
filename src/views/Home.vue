<template>
  <v-card
    v-if="!contextStore.loading"
    class="border-sm px-6"
  >
    <v-card-title>
      <PageTitle
        :icon="mdiVideoPlus"
        :text="pageTitle"
      />
    </v-card-title>
    <v-card-text>
      <Spinner v-if="refreshingCourses" />
      <template v-if="!refreshingCourses">
        <div class="opt-in-banner mb-4" role="note" aria-label="Course Capture opt-in change notice">
          <p class="m-0">
            <strong>Course Capture has changed for 2026.</strong>
            You must opt in for your courses to be recorded.
            For more information, visit our
            <a
              :href="gettingStartedUrl"
              target="_blank"
              rel="noopener"
              class="opt-in-banner__link"
            >
              Instructor Getting Started Guide
            </a>.
          </p>
        </div>
        <v-row
          v-for="(courses, index) in [eligibleCourses, ineligibleCourses]"
          :key="index"
          :aria-labelledby="`${getTableId(index)}-header`"
          role="region"
        >
          <h2 :id="`${getTableId(index)}-header`" class="pt-4 px-4 text-medium-emphasis w-100">
            <template v-if="index === 0">
              Courses eligible for capture
            </template>

            <!-- Collapsible header for in-eligible courses -->
            <button
              v-if="index !== 0 && courses.length"
              class="text-left"
              type="button"
              :aria-expanded="showIneligible"
              :aria-controls="getTableId(index)"
              :aria-label="showIneligible
                ? 'Collapse courses not in a course capture classroom'
                : 'Expand courses not in a course capture classroom'"
              style="all: unset; cursor: pointer;"
              @click="showIneligible = !showIneligible"
            >
              Courses not in a course capture classroom
              <span aria-hidden="true"> {{ showIneligible ? '[-]' : '[+]' }} </span>
            </button>
          </h2>
          <div v-if="index === 0 || showIneligible" class="overflow-x-auto px-md-4 w-100">
            <div v-if="isEmpty(courses)" class="px-4 pt-2">No courses.</div>
            <v-data-table
              v-if="size(courses)"
              :id="getTableId(index)"
              class="instructor-courses overflow-y-visible"
              disable-sort
              :headers="index === 0 ? eligibleHeaders : ineligibleHeaders"
              hide-default-footer
              :items="courses"
              :items-per-page="-1"
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
                    <span class="font-size-13 font-weight-bold">{{ column.title }}</span>
                  </th>
                </tr>
              </template>
              <template #body="{items}">
                <!-- eslint-disable-next-line vue/no-v-for-template-key -->
                <template v-for="course in items" :key="course.sectionId">
                  <tr
                    :id="`${getTableId(index)}-${course.sectionId}`"
                    class="clickable-row"
                    tabindex="0"
                    role="link"
                    :aria-label="`View details for ${course.courseCodes?.[0] || 'course'}`"
                    @click="goToCourse(course.sectionId)"
                    @keydown.enter.prevent="goToCourse(course.sectionId)"
                    @keydown.space.prevent="goToCourse(course.sectionId)"
                  >
                    <td
                      :id="`course-${course.sectionId}-status`"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
                      columnheader="courses-table-status-th"
                    >
                      <div v-if="course.statusLabel === 'Canceled'" class="canceled-indicator d-flex">
                        <v-icon color="error" :icon="mdiClose" />
                        <span class="font-weight-bold text-no-wrap text-error">{{ course.statusLabel }}</span>
                      </div>
                      <div v-else>
                        <v-tooltip
                          :text="getStatusTooltip(course.statusLabel)"
                          location="top"
                        >
                          <template #activator="{ props }">
                            <span v-bind="props" class="text-no-wrap">{{ course.statusLabel }}</span>
                          </template>
                        </v-tooltip>
                      </div>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-label`"
                      :aria-rowspan="size(course.displayMeetings)"
                      class="text-no-wrap"
                      :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-b-0': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-label-th`"
                    >
                      <div v-for="(courseCode, courseCodeIndex) in course.courseCodes" :key="courseCode">
                        <router-link
                          v-if="courseCodeIndex === 0"
                          :id="`link-course-${course.sectionId}`"
                          class="course-link"
                          :to="`/course/${config.currentTermId}/${course.sectionId}`"
                          @click.stop
                        >
                          {{ courseCode }}
                        </router-link>
                        <span v-if="courseCodeIndex > 0">{{ courseCode }}</span>
                      </div>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-title`"
                      :aria-rowspan="size(course.displayMeetings)"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-title-th`"
                    >
                      <span aria-hidden="true">{{ course.courseTitle || '&mdash;' }}</span>
                      <span class="sr-only">{{ course.courseTitle || 'blank' }}</span>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-instructors`"
                      :aria-rowspan="size(course.displayMeetings)"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-instructors-th`"
                    >
                      {{ oxfordJoin(map(course.instructors, 'name')) }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-room-0`"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
                      :columnheader="`${getTableId(index)}-room-th`"
                    >
                      {{ course.displayMeetings[0].room.location }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-days-0`"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-days-th`"
                    >
                      <Days v-if="size(course.displayMeetings[0].daysNames)" :names-of-days="course.displayMeetings[0].daysNames" />
                      <span v-if="isEmpty(course.displayMeetings[0].daysNames)">&mdash;</span>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-time-0`"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
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
                  </tr>
                  <tr
                    v-for="(meeting, meetingIndex) in tail(course.displayMeetings)"
                    :id="`${getTableId(index)}-${course.sectionId}-${meetingIndex}`"
                    :key="`${course.sectionId}-${meetingIndex}`"
                    class="clickable-row"
                    tabindex="0"
                    role="link"
                    :aria-label="`View details for ${course.courseCodes?.[0] || 'course'}`"
                    @click="goToCourse(course.sectionId)"
                    @keydown.enter.prevent="goToCourse(course.sectionId)"
                    @keydown.space.prevent="goToCourse(course.sectionId)"
                  >
                    <td :aria-hidden="true" colspan="4" />
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
                    <td v-if="index === 0" :aria-hidden="true" />
                  </tr>
                </template>
              </template>
            </v-data-table>
          </div>
        </v-row>
      </template>
      <v-divider class="my-12" />
      <CourseCapturePreferences
        :uid="currentUser.uid"
        :initial-opt-in-new-courses="currentUser.optInNewCourses"
        :initial-do-not-email="currentUser.doNotEmail"
        :disable-email-because-courses="anyCourseOptedInOrScheduled"
      />
    </v-card-text>
  </v-card>
</template>

<script lang="ts" setup>
import {DateTime} from 'luxon'
import {each, get, isEmpty, map, size, tail} from 'lodash'
import {mdiClose, mdiVideoPlus} from '@mdi/js'
import {computed, onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import {useRouter} from 'vue-router'
import {oxfordJoin, partitionCoursesByEligibility, pluralize} from '@/lib/utils'
import {getCourseCodes, getDisplayMeetings} from '@/lib/berkeley'
import type {Course} from '@/lib/types'
import Days from '@/components/util/Days.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import Spinner from '@/components/util/Spinner.vue'
import {useContextStore} from '@/stores/context'
import CourseCapturePreferences from '@/components/course/CourseCapturePreferences.vue'

const router = useRouter()

const contextStore = useContextStore()
const {config, currentUser} = storeToRefs(contextStore)
const eligibleCourses = ref<Course[]>([])
const ineligibleCourses = ref<Course[]>([])
const ineligibleHeaders = [
  {title: 'Status', value: 'status'},
  {title: 'Course', value: 'label'},
  {title: 'Title', value: 'title'},
  {title: 'Instructors', value: 'instructors'},
  {title: 'Room', value: 'room'},
  {title: 'Days', value: 'days'},
  {title: 'Time', value: 'time'},
]
const eligibleHeaders = [
  ...ineligibleHeaders
]
const pageTitle = ref('')
const refreshingCourses = ref(false)

const showIneligible = ref(false)

const isScheduled = (c) => Array.isArray(c.scheduled) ? c.scheduled.length > 0 : !!c.scheduled

const anyCourseOptedInOrScheduled = computed(() => {
  return [...eligibleCourses.value] .some(c => c.hasOptedIn || isScheduled(c))
})

const gettingStartedUrl = computed(() =>
  get(config.value, 'instructorGettingStartedUrl', 'https://rtl.berkeley.edu/services-programs/course-capture/instructor-getting-started')
)

contextStore.loadingStart()

onMounted(() => {
  refreshCourses()
  pageTitle.value = `Your ${config.value.currentTermName} ${pluralize('Course', size(currentUser.value.courses), false)}`
  contextStore.loadingComplete(pageTitle.value)
})

const goToCourse = (sectionId: string | number) => {
  router.push(`/course/${config.value.currentTermId}/${sectionId}`)
}

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

    const eligibleLen = get(course, 'meetings.eligible.length', 0)
    const instructors = get(course, 'instructors', []) || []
    const totalInstructors = instructors.length
    const optedInCount = instructors.filter(i => i?.hasOptedIn).length
    const anyOpted = optedInCount > 0
    const allOpted = totalInstructors > 0 && optedInCount === totalInstructors
    const partialOptIn = totalInstructors > 1 && anyOpted && !allOpted

    course.statusLabel = course.deletedAt
      ? 'Canceled'
      : (isScheduled(course)
        ? 'Scheduled'
        : (eligibleLen > 0
          ? (partialOptIn
            ? 'Partial Opt-in'
            : (allOpted ? 'Pending' : 'Not Scheduled'))
          : 'Not Eligible'))
  })
}

const getStatusTooltip = (label) => {
  if (label === 'Pending') {
    return 'Recordings will be scheduled within an hour.'
  } else if (label === 'Not Scheduled') {
    return 'Recordings are not scheduled. One or more instructors have not opted in.'
  } else {
    return label
  }
}

</script>

<style>
.instructor-courses .v-table__wrapper {
  overflow: visible !important;
}

.course-link {
  text-decoration: underline !important;
  text-underline-offset: 2px;
  cursor: pointer;
}
.v-selection-control--disabled .v-label {
  opacity: 0.6;
}
.opt-in-banner {
  background-color: rgb(var(--v-theme-surface));          /* light blue */
  border: 1px solid #b3dcff;     /* subtle blue border */
  border-radius: 8px;            /* slightly rounded edges */
  padding: 12px 16px;
  line-height: 1.4;
  width: 1200px;
}

.opt-in-banner__link {
  text-decoration: underline;
  text-underline-offset: 2px;
}
.clickable-row { cursor: pointer; }
.clickable-row:hover { background-color: rgba(0, 0, 0, 0.03); }
.clickable-row:focus {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -2px;
}
</style>
