<template>
  <v-card
    v-if="!contextStore.loading"
    class="border-sm"
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
        <v-row
          v-for="(courses, index) in [eligibleCourses, ineligibleCourses]"
          :key="index"
          :aria-labelledby="`${getTableId(index)}-header`"
          class="py-5"
          role="region"
        >
          <h2 :id="`${getTableId(index)}-header`" class="pa-4 text-medium-emphasis w-100">
            <template v-if="index === 0">
              Courses eligible for capture
            </template>

            <!-- Collapsible header for in-eligible courses -->
            <button
              v-else
              class="text-left"
              type="button"
              :aria-expanded="showIneligible.toString()"
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
                  <tr :id="`${getTableId(index)}-${course.sectionId}`">
                    <td
                      v-if="index === 0"
                      :id="`${getTableId(index)}-${course.sectionId}-hasOptedIn`"
                      :aria-rowspan="size(course.displayMeetings)"
                      :class="{'border-b-0': size(course.displayMeetings) > 1}"
                      class="text-no-wrap"
                    >
                      <ToggleOptIn
                        :aria-label="`Opt out course ${get(course.courseCodes, '0', course.title)}.`"
                        :disabled="course.hasBlanketOptedOut"
                        :initial-value="course.hasOptedIn"
                        :instructor-uids="[currentUser.uid]"
                        label=""
                        :section-id="`${course.sectionId}`"
                        :term-id="`${course.termId}`"
                        :on-toggle="onToggleOptIn"
                      />
                    </td>
                    <td :id="`course-${course.sectionId}-status`" columnheader="courses-table-status-th">
                      <div v-if="course.statusLabel === 'Canceled'" class="canceled-indicator d-flex">
                        <v-icon color="error" :icon="mdiClose" />
                        <span class="font-weight-bold text-error">{{ course.statusLabel }}</span>
                      </div>
                      <div v-else>
                        <v-tooltip
                          v-if="['Pending', 'Waiting on co-instructor'].includes(course.statusLabel)"
                          :text="getStatusTooltip(course.statusLabel)"
                          location="top"
                        >
                          <template #activator="{ props }">
                            <span v-bind="props">{{ course.statusLabel }}</span>
                          </template>
                        </v-tooltip>
                        <span v-else>{{ course.statusLabel }}</span>
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
                  <tr v-for="(meeting, meetingIndex) in tail(course.displayMeetings)" :id="`${getTableId(index)}-${course.sectionId}-${meetingIndex}`" :key="`${course.sectionId}-${meetingIndex}`">
                    <td :aria-hidden="true" colspan="3" />
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
      <v-divider class="my-2" />

      <section aria-labelledby="future-courses-header" class="py-5">
        <h2 id="future-courses-header" class="pa-4 text-medium-emphasis w-100">
          Future courses
        </h2>

        <div class="px-md-4 w-100">
          <v-radio-group
            v-model="futureCoursesPref"
            :aria-labelledby="'future-courses-header'"
            @update:model-value="onFutureCoursesPreferenceChange"
          >
            <v-radio
              id="all-future-courses-opt-in"
              value="all"
              color="primary"
              label="I want all my future courses to be opted into Course Capture by default"
            />
            <v-radio
              id="choose-courses-opt-in"
              value="choose"
              color="primary"
              label="I want to choose whether or not to opt in future courses to Course Capture"
            />
          </v-radio-group>
        </div>
      </section>
      <v-divider class="my-2" />

      <section aria-labelledby="email-settings-header" class="py-5">
        <h2 id="email-settings-header" class="pa-4 text-medium-emphasis w-100">
          Email settings
        </h2>

        <div class="px-md-4 w-100">
          <v-checkbox
            id="email-checkbox"
            v-model="emailReceive"
            :disabled="isEmailDisabled"
            :aria-labelledby="'email-settings-header'"
            label="I want to receive emails from Course Capture (required if opted-in to current or future courses)"
            @update:model-value="onEmailReceiveChange"
          />
        </div>
      </section>
    </v-card-text>
  </v-card>
</template>

<script lang="ts" setup>
import {DateTime} from 'luxon'
import {each, get, isEmpty, map, size, tail} from 'lodash'
import {mdiClose, mdiVideoPlus} from '@mdi/js'
import {computed, onMounted, ref, watch} from 'vue'
import {storeToRefs} from 'pinia'
import {alertScreenReader, oxfordJoin, partitionCoursesByEligibility, pluralize} from '@/lib/utils'
import {getCourseCodes, getDisplayMeetings} from '@/lib/berkeley'
import Days from '@/components/util/Days'
import PageTitle from '@/components/util/PageTitle'
import Spinner from '@/components/util/Spinner'
import ToggleOptIn from '@/components/course/ToggleOptIn'
import {useContextStore} from '@/stores/context'
import {updateDoNotEmail, updateOptInNewCourses} from '@/api/user'

const contextStore = useContextStore()
const {config, currentUser} = storeToRefs(contextStore)
const eligibleCourses = ref([])
const ineligibleCourses = ref([])
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
  {title: 'Opt In', value: 'hasOptedIn'},
  ...ineligibleHeaders
]
const pageTitle = ref('')
const refreshingCourses = ref(false)

const showIneligible = ref(false)
const futureCoursesPref = ref(null)
const emailReceive = ref(true)

// Track current-course opt-ins *only* from ToggleOptIn callbacks
const optedInCount = ref(0)
const _optedInSet = new Set<string>()

// Email is disabled if: (a) user opted ALL future courses in OR (b) any current course is opted in
const isEmailDisabled = computed(() => {
  const futureAll = futureCoursesPref.value === 'all'
  const anyCurrentOptIn = optedInCount.value > 0
  return futureAll || anyCurrentOptIn
})

watch(isEmailDisabled, (required) => {
  if (required) {
    emailReceive.value = true
    if (currentUser.value.doNotEmail) {
      onEmailReceiveChange(true, {force: true})
    }
  }
})

contextStore.loadingStart()

onMounted(() => {
  refreshCourses()
  pageTitle.value = `Your ${config.value.currentTermName} ${pluralize('Course', size(currentUser.value.courses), false)}`
  futureCoursesPref.value = currentUser.value.optInNewCourses ? 'all' : 'choose'
  emailReceive.value = !currentUser.value.doNotEmail
  contextStore.loadingComplete(pageTitle.value)
})

const onToggleOptIn = (_msgOrEvent, payload) => {
  const sectionId = payload?.sectionId
  const optedIn = !!payload?.optedIn
  if (!sectionId) return
  const had = _optedInSet.has(sectionId)
  if (optedIn && !had) {
    _optedInSet.add(sectionId)
    optedInCount.value++
  } else if (!optedIn && had) {
    _optedInSet.delete(sectionId)
    optedInCount.value--
  }
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
    course.statusLabel = course.deletedAt
      ? 'Canceled'
      : (course.scheduled
        ? 'Scheduled'
        : (get(course, 'meetings.eligible.length', 0) > 0 ? 'Not Scheduled' : 'Not Eligible'))
  })
}

const getStatusTooltip = (label) => {
  if (label === 'Pending') {
    return 'Recordings will be scheduled within an hour'
  }
  // label === 'Waiting on co-instructor'
  return 'Recordings are not scheduled. A co-instructor has not opted in'
}

const onFutureCoursesPreferenceChange = (value) => {
  const optInNewCourses = value === 'all'

  updateOptInNewCourses(currentUser.value.uid, {optInNewCourses})
    .then((prefs) => {
      const {optInNewCourses: optAll, doNotEmail} = prefs

      futureCoursesPref.value = optAll ? 'all' : 'choose'
      if (typeof doNotEmail === 'boolean') {
        currentUser.value.doNotEmail = doNotEmail
        emailReceive.value = !doNotEmail
      }

      currentUser.value.optInNewCourses = !!optAll

      alertScreenReader('Future courses preference updated.')
    })
    .catch(() => {
      alertScreenReader('Failed to update future courses preference.')
    })
}

const onEmailReceiveChange = (value, {force = false} = {}) => {
  if (isEmailDisabled.value && !force) {
    emailReceive.value = true
    return
  }
  const body = {doNotEmail: !value}
  updateDoNotEmail(currentUser.value.uid, body)
    .then((prefs) => {
      if (typeof prefs?.doNotEmail === 'boolean') {
        currentUser.value.doNotEmail = prefs.doNotEmail
        emailReceive.value = !prefs.doNotEmail
      }
      if (typeof prefs?.optInNewCourses === 'boolean') {
        currentUser.value.optInNewCourses = prefs.optInNewCourses
        futureCoursesPref.value = prefs.optInNewCourses ? 'all' : 'choose'
      }
      alertScreenReader('Email preference updated.')
    })
    .catch(() => {
      alertScreenReader('Failed to update email preference.')
    })
}
</script>

<style>
.instructor-courses .v-table__wrapper {
  overflow: visible !important;
}

.instructor-courses .course-link {
  text-decoration: underline;
  text-underline-offset: 2px;
}
.v-selection-control--disabled .v-label {
  opacity: 0.6;
}
</style>
