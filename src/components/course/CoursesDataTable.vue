<template>
  <div>
    <v-row id="courses-data-table-message" class="text-medium-emphasis pb-1 px-4">
      <v-spacer />
      <v-col cols="12" md="6"><span v-if="!refreshing && !searchText">{{ description }}</span></v-col>
    </v-row>
    <v-data-table
      id="courses-data-table"
      v-model="selectedRows"
      :disable-sort="courses.length < 2"
      :headers="headers"
      :items="courses"
      :items-per-page="contextStore.config.searchItemsPerPage"
      :loading="refreshing"
      must-sort
      :page.sync="pageCurrent"
      :search="searchText"
      :sort-by="[sortBy]"
      @update:sort-by="onUpdateSortBy"
    >
      <template #headers="{columns, isSorted, toggleSort, getSortIcon}">
        <tr>
          <th
            v-for="(column, index) in columns"
            :id="`courses-table-${column.key}-th`"
            :key="index"
            :aria-label="column.title"
            :aria-sort="isSorted(column) ? `${sortBy.order}ending` : null"
            class="text-start text-no-wrap"
            :class="{'sortable': column.sortable === false}"
            scope="col"
          >
            <template v-if="column.sortable && courses.length >= 2">
              <v-btn
                :id="`courses-table-sort-by-${column.key}-btn`"
                :append-icon="getSortIcon(column)"
                :aria-label="`Sort by ${column.title} ${isSorted(column) && sortBy.order === 'asc' ? 'descending' : 'ascending'}`"
                class="font-size-12 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
                :class="{'icon-visible': isSorted(column)}"
                color="body"
                density="compact"
                :disabled="refreshing"
                variant="plain"
                @click="() => toggleSort(column)"
              >
                <span class="text-left text-wrap">{{ column.title }}</span>
              </v-btn>
            </template>
            <template v-else>
              <span class="font-size-12 font-weight-bold py-1 text-align-center text-medium-emphasis text-transform-unset v-btn" :class="{'opacity-30': refreshing}">
                {{ column.title }}
              </span>
            </template>
          </th>
        </tr>
      </template>
      <template #body="{items}">
        <tr v-if="refreshing">
          <td class="pa-12 text-center" :colspan="headers.length">
            <v-progress-circular
              class="spinner"
              :indeterminate="true"
              rotate="5"
              size="64"
              width="4"
              color="primary"
            ></v-progress-circular>
          </td>
        </tr>
        <tr v-if="!refreshing && !items.length" class="py-5 text-center text-subtitle-1">
          <td id="message-when-zero-courses" :colspan="headers.length">
            No courses.
          </td>
        </tr>
        <template v-if="!refreshing && items.length">
          <!-- eslint-disable-next-line vue/no-v-for-template-key -->
          <template v-for="course in items" :key="course.sectionId">
            <tr>
              <td
                :id="`course-name-${course.sectionId}`"
                :aria-rowspan="size(course.displayMeetings)"
                :class="tdc(course)"
                columnheader="courses-table-course-th"
              >
                <div v-for="(courseCode, courseCodeIndex) in course.courseCodes" :key="courseCode">
                  <router-link
                    v-if="courseCodeIndex === 0"
                    :id="`link-course-${course.sectionId}`"
                    :to="`/course/${contextStore.config.currentTermId}/${course.sectionId}`"
                  >
                    <span :class="{'line-through': course.deletedAt}">{{ courseCode }}</span>
                  </router-link>
                  <span v-if="courseCodeIndex > 0">{{ courseCode }}</span>
                </div>
              </td>
              <td :id="`section-id-${course.sectionId}`" :class="tdc(course)" columnheader="courses-table-section-th">{{ course.sectionId }}</td>
              <td v-if="includeRoomColumn" :class="tdc(course)" columnheader="courses-table-room-th">
                <div v-if="course.room && course.room.id" :class="{'line-through': course.deletedAt}">
                  <router-link
                    :id="`course-${course.sectionId}-room-${course.room.id}`"
                    :to="`/room/${course.room.id}`"
                  >
                    {{ course.room.location }}
                  </router-link>
                </div>
                <span v-if="course.room && course.room.location && !course.room.id" :class="{'line-through': course.deletedAt}">
                  {{ course.room.location }}
                </span>
                <span v-if="!course.room">&mdash;</span>
              </td>
              <td :id="`meeting-days-${course.sectionId}-0`" :class="tdc(course)" columnheader="courses-table-days-th">
                <div :class="{'line-through': course.deletedAt}">
                  <Days v-if="get(course, 'displayMeetings.0.daysNames.length')" :names-of-days="course.displayMeetings[0].daysNames" />
                  <span v-else>&mdash;</span>
                </div>
              </td>
              <td :id="`meeting-times-${course.sectionId}-0`" :class="tdc(course)" columnheader="courses-table-time-th">
                <div :class="{'line-through': course.deletedAt}">
                  <div v-if="course.nonstandardMeetingDates">
                    <span class="text-no-wrap">
                      {{ DateTime
                        .fromISO(get(course, 'displayMeetings.0.startDate'))
                        .toFormat('MMM d, yyyy') }} -
                    </span>
                    <span class="sr-only">to</span>
                    <span class="text-no-wrap">
                      {{ DateTime
                        .fromISO(get(course, 'displayMeetings.0.endDate'))
                        .toFormat('MMM d, yyyy') }} -
                    </span>
                  </div>
                  <span aria-hidden="true" class="text-no-wrap">{{ get(course, 'displayMeetings.0.startTimeFormatted') }} - {{ get(course, 'displayMeetings.0.endTimeFormatted') }}</span>
                  <span class="sr-only">{{ get(course, 'displayMeetings.0.startTimeFormatted') }} to {{ get(course, 'displayMeetings.0.endTimeFormatted') }}</span>
                </div>
              </td>
              <td :id="`course-${course.sectionId}-status`" :class="tdc(course)" columnheader="courses-table-status-th">
                <div v-if="course.deletedAt">
                  <v-icon
                    color="red"
                    class="font-weight-bold pb-1 pl-0"
                    :icon="mdiClose"
                  />
                  <span class="font-weight-bold red--text">Canceled</span>
                </div>
                <div v-if="!course.deletedAt && course.scheduled">
                  Scheduled
                </div>
                <div v-if="!course.deletedAt && !course.scheduled && course.meetings.eligible.length">
                  Not Scheduled
                </div>
                <div v-if="!course.deletedAt && !course.scheduled && !course.meetings.eligible.length">
                  Not Eligible
                </div>
              </td>
              <td :class="tdc(course)" columnheader="courses-table-instructors-th">
                <div v-if="course.instructors.length">
                  <div v-for="instructor in course.instructors" :key="instructor.uid" class="mb-1 mt-1">
                    <Instructor :course="course" :instructor="instructor" />
                  </div>
                </div>
                <div v-if="!course.instructors.length">
                  &mdash;
                </div>
              </td>
              <td :id="`course-${course.sectionId}-publish-types`" :class="tdc(course)" columnheader="courses-table-publish-th">
                <span aria-hidden="true">{{ (course.scheduled && course.publishTypeName) || '&mdash;' }}</span>
                <span class="sr-only">{{ (course.scheduled && course.publishTypeName) || 'blank' }}</span>
              </td>
              <td v-if="includeOptOutColumnForUid" :class="tdc(course)">
                <ToggleOptOut
                  :key="course.sectionId"
                  :term-id="`${course.termId}`"
                  :section-id="`${course.sectionId}`"
                  :instructor-uid="includeOptOutColumnForUid"
                  :initial-value="course.hasOptedOut"
                  :disabled="course.hasBlanketOptedOut"
                  :on-toggle="onToggleOptOut(course)"
                />
              </td>
            </tr>
            <tr v-for="(meeting, meetingIndex) in tail(course.displayMeetings)" :key="`${course.sectionId}-${meetingIndex}`">
              <td :aria-hidden="true" colspan="2" :class="tdcLower(course)"></td>
              <td v-if="includeRoomColumn" :class="tdcLower(course)">
                <router-link
                  v-if="meeting.room"
                  :id="`course-${course.sectionId}-room-${meeting.room.id}`"
                  :to="`/room/${meeting.room.id}`"
                >
                  {{ meeting.room.location }}
                </router-link>
                <span v-if="!meeting.room">&mdash;</span>
              </td>
              <td class="text-no-wrap" :class="tdcLower(course)">
                <Days v-if="meeting.daysNames.length" :names-of-days="meeting.daysNames" />
                <span v-if="!meeting.daysNames.length">&mdash;</span>
              </td>
              <td class="text-no-wrap" :class="tdcLower(course)">
                <div v-if="course.nonstandardMeetingDates">
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
                <div :class="{'pb-2': course.nonstandardMeetingDates && meetingIndex === course.displayMeetings.length - 1}">
                  <span aria-hidden="true">{{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}</span>
                  <span class="sr-only">{{ meeting.startTimeFormatted }} to {{ meeting.endTimeFormatted }}</span>
                </div>
              </td>
              <td :aria-hidden="true" colspan="3" :class="tdcLower(course)"></td>
            </tr>
            <tr v-if="course.scheduled" :key="`approvals-${course.sectionId}`">
              <td :colspan="headers.length" class="pb-2">
                <div v-if="course.scheduled" class="pb-3">
                  Recordings scheduled on {{
                    DateTime
                      .fromISO(course.scheduled[0].createdAt)
                      .toFormat('MMM d, yyyy')
                  }}.
                  They will be published to {{
                    course.scheduled[0]
                      .publishTypeName
                      .replace('Publish to ', '')
                  }}.
                </div>
              </td>
            </tr>
          </template>
        </template>
      </template>
      <template #bottom="{pageCount}">
        <div v-if="!refreshing && pageCount > 1" class="text-center pb-4 pt-2">
          <v-pagination
            id="ouija-pagination"
            v-model="pageCurrent"
            :length="pageCount"
          ></v-pagination>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script setup>
import {DateTime} from 'luxon'
import {each, filter, get, map, size, tail} from 'lodash'
import {mdiClose} from '@mdi/js'
import {onMounted, ref, watch} from 'vue'
import {alertScreenReader} from '@/lib/utils'
import Days from '@/components/util/Days'
import Instructor from '@/components/course/Instructor'
import ToggleOptOut from '@/components/course/ToggleOptOut'
import {getDisplayMeetings} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

const props = defineProps({
  courses: {
    required: true,
    type: Array
  },
  description: {
    default: undefined,
    type: String
  },
  includeOptOutColumnForUid: {
    required: false,
    type: String,
    default: undefined
  },
  includeRoomColumn: {
    required: true,
    type: Boolean
  },
  onToggleOptOut: {
    required: false,
    type: Function,
    default: () => {}
  },
  refreshing: {
    required: true,
    type: Boolean
  },
  searchText: {
    default: undefined,
    type: String
  }
})

const contextStore = useContextStore()
const headers = ref([
  {key: 'course', title: 'Course', sortable: true, value: 'label'},
  {key: 'section', title: 'Section', sortable: true, value: 'sectionId', class: 'w-10'},
  {key: 'room', title: 'Room', sortable: true, value: 'room.location'},
  {key: 'days', title: 'Days', sortable: false},
  {key: 'time', title: 'Time', sortable: false},
  {key: 'status', title: 'Status', class: 'w-10', sortable: false},
  {key: 'instructors', title: 'Instructor(s)', value: 'instructorNames', sortable: false},
  {key: 'publish', title: 'Publish', sortable: true, value: 'publishTypeName', class: 'w-10'},
  {key: 'optOut', title: 'Opt out', value: 'hasOptedOut', sortable: false}
])
const pageCurrent = ref(1)
const selectedRows = ref([])
const sortBy = ref({})

watch(() => props.refreshing, async(value) => {
  if (!value) {
    // False value means that the refresh just ended in the parent component and we can proceed.
    refresh()
  }
})

onMounted(() => {
  if (!props.includeRoomColumn) {
    headers.value = filter(headers.value, h => h.title !== 'Room')
  }
  if (!props.includeOptOutColumnForUid) {
    headers.value = filter(headers.value, h => h.title !== 'Opt out')
  }
  refresh()
})

const onUpdateSortBy = primarySortBy => {
  const key = primarySortBy[0].key
  const header = find(headers.value, {key: key})
  sortBy.value = primarySortBy[0]
  pageCurrent.value = 1
  if (header) {
    alertScreenReader(`Sorted by ${header.title}, ${sortBy.value.order}ending`)
  }
}

const refresh = () => {
  pageCurrent.value = 1
  each(props.courses, course => {
    course.instructorNames = map(course.instructors, 'name')
    course.isSelectable = !course.hasOptedOut
    const meetings = getDisplayMeetings(course)
    course.displayMeetings = meetings
    course.room = meetings.length && meetings[0].room ? meetings[0].room : null
  })
}

const tdc = course => {
  return {
    'border-bottom-zero': getDisplayMeetings(course).length > 1 || course.scheduled,
    'pt-3 pb-3': size(course.courseCodes) > 1
  }
}

const tdcLower = course => {
  return {
    'border-bottom-zero': course.scheduled
  }
}
</script>
