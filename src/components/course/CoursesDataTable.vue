<template>
  <div aria-describedby="courses-data-table-message" aria-label="Courses table" role="region">
    <v-row id="courses-data-table-message" class="text-medium-emphasis pb-1 px-4 mb-1">
      <span class="ml-4">{{ messageForCourses }}</span>
      <v-spacer />
      <v-col class="text-right" cols="12" md="6"><span v-if="!refreshing && !searchText">{{ description }}</span></v-col>
    </v-row>
    <v-data-table
      id="courses-data-table"
      v-model="selectedRows"
      v-model:page="page"
      :disable-sort="courses.length < 2"
      :headers="headers"
      :items="courses"
      :items-per-page="contextStore.config.searchItemsPerPage"
      :loading="refreshing"
      must-sort
      :search="searchText"
      :sort-by="[sortBy]"
      @update:sort-by="onUpdateSortBy"
    >
      <template #headers="{columns, isSorted, toggleSort, getSortIcon}">
        <tr>
          <th
            v-for="(column, index) in columns"
            :id="`courses-table-${normalizeId(column.key)}-th`"
            :key="index"
            :aria-label="column.screenreaderTitle || column.title"
            :aria-sort="isSorted(column) ? `${sortBy.order}ending` : null"
            class="text-start"
            :class="{'sortable': column.sortable === false}"
            scope="col"
          >
            <template v-if="column.sortable && courses.length >= 2">
              <v-btn
                :id="`courses-table-sort-by-${column.key}-btn`"
                :append-icon="getSortIcon(column)"
                :aria-label="`Sort by ${column.title} ${isSorted(column) && sortBy.order === 'asc' ? 'descending' : 'ascending'}`"
                class="font-size-13 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
                :class="{'icon-visible': isSorted(column)}"
                density="compact"
                :disabled="refreshing"
                variant="plain"
                @click="() => toggleSort(column)"
              >
                <span class="text-left text-wrap">{{ column.title }}</span>
              </v-btn>
            </template>
            <template v-else>
              <span
                v-if="column.screenreaderTitle"
                aria-hidden="true"
                class="font-size-13 font-weight-bold py-1 text-align-center text-medium-emphasis text-transform-unset v-btn"
                :class="{'opacity-30': refreshing}"
              >
                {{ column.title }}
              </span>
              <span
                v-if="!column.screenreaderTitle"
                class="font-size-13 font-weight-bold py-1 text-align-center text-medium-emphasis text-transform-unset v-btn"
                :class="{'opacity-30': refreshing}"
              >
                {{ column.title }}
              </span>
            </template>
          </th>
        </tr>
      </template>
      <template #body="{items}">
        <tr v-if="refreshing" id="course-table-is-refreshing">
          <td class="pa-12 text-center" :colspan="headers.length">
            <v-progress-circular
              class="spinner"
              :indeterminate="true"
              rotate="5"
              size="64"
              width="4"
              color="primary"
            />
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
            <tr :id="`tr-course-${course.sectionId}`">
              <td
                v-if="showOptIn"
                :id="`td-course-${course.sectionId}-opt-in-status`"
                :class="tdc(course)"
                data-label="Status"
              >
                <span v-if="course.statusLabel !== 'Not Eligible'">
                  {{ getOptInStatus(course) }}
                </span>
              </td>
              <td
                :id="`td-course-${course.sectionId}-name`"
                :aria-rowspan="size(course.displayMeetings)"
                :class="tdc(course)"
                data-label="Course"
              >
                <div v-for="(courseCode, courseCodeIndex) in course.courseCodes" :key="courseCode">
                  <router-link
                    v-if="courseCodeIndex === 0"
                    :id="`link-course-${course.sectionId}`"
                    :to="`/course/${contextStore.config.currentTermId}/${course.sectionId}`"
                  >
                    <span :class="{'line-through': course.deletedAt}">{{ courseCode }}<span v-if="course.deletedAt" class="sr-only">&nbsp;(canceled)</span></span>
                  </router-link>
                  <span v-if="courseCodeIndex > 0">{{ courseCode }}</span>
                </div>
              </td>
              <td
                :id="`td-course-${course.sectionId}-section-id`"
                :class="tdc(course)"
                data-label="Section"
              >
                {{ course.sectionId }}
              </td>
              <td
                v-if="includeRoomColumn"
                :id="`td-course-${course.sectionId}-meeting-room-${get(course.room, 'id', 'none')}`"
                :class="tdc(course)"
                data-label="Room"
              >
                <div v-if="course.room && course.room.id" :class="{'line-through': course.deletedAt}">
                  <router-link
                    :id="`course-${course.sectionId}-room-${course.room.id}`"
                    :to="`/room/${course.room.id}`"
                  >
                    {{ course.room.location }}<span v-if="course.deletedAt" class="sr-only">&nbsp;(canceled)</span>
                  </router-link>
                </div>
                <span v-if="course.room && course.room.location && !course.room.id" :class="{'line-through': course.deletedAt}">
                  {{ course.room.location }}
                </span>
                <span v-if="!course.room">&mdash;</span>
              </td>
              <td
                :id="`td-course-${course.sectionId}-meeting-room-${get(course.room, 'id', 'none')}-days-of-week`"
                :class="tdc(course)"
                data-label="Days"
              >
                <div :class="{'line-through': course.deletedAt}">
                  <Days v-if="get(course, 'displayMeetings.0.daysNames.length')" :names-of-days="course.displayMeetings[0].daysNames" />
                  <span v-else>&mdash;</span>
                </div>
              </td>
              <td
                :id="`td-course-${course.sectionId}-meeting-room-${get(course.room, 'id', 'none')}-dates`"
                :class="tdc(course)"
                data-label="Time"
              >
                <div :class="{'line-through': course.deletedAt}">
                  <div v-if="course.nonstandardMeetingDates && get(course, 'displayMeetings.0.startDate') && get(course, 'displayMeetings.0.endDate')">
                    <Date :date="course.displayMeetings[0].startDate" />
                    <span :aria-hidden="true"> - </span>
                    <span class="sr-only"> to </span>
                    <Date :date="course.displayMeetings[0].endDate" />
                  </div>
                  <span aria-hidden="true">{{ get(course, 'displayMeetings.0.startTimeFormatted') }} - {{ get(course, 'displayMeetings.0.endTimeFormatted') }}</span>
                  <span class="sr-only">{{ get(course, 'displayMeetings.0.startTimeFormatted') }} to {{ get(course, 'displayMeetings.0.endTimeFormatted') }}</span>
                </div>
              </td>
              <td
                :id="`td-course-${course.sectionId}-status`"
                :class="tdc(course)"
                data-label="Status"
              >
                <div v-if="course.statusLabel === 'Canceled'" class="canceled-indicator d-flex">
                  <v-icon color="error" :icon="mdiClose" />
                  <span class="font-weight-bold text-error">{{ course.statusLabel }}</span>
                </div>
                <div v-else>
                  {{ course.statusLabel }}
                </div>
              </td>
              <td
                :id="`td-course-${course.sectionId}-instructors`"
                :class="tdc(course)"
                data-label="Instructor(s)"
              >
                <div v-if="course.instructors.length">
                  <div v-for="instructor in course.instructors" :key="instructor.uid" class="mb-1 mt-1">
                    <Instructor :course="course" :instructor="instructor" />
                  </div>
                </div>
                <div v-if="!course.instructors.length">
                  &mdash;
                </div>
              </td>
              <td
                :id="`td-course-${course.sectionId}-publish-types`"
                :class="tdc(course)"
                data-label="Publish"
              >
                <span aria-hidden="true">{{ (course.scheduled && course.publishTypeName) || '&mdash;' }}</span>
                <span class="sr-only">{{ (course.scheduled && course.publishTypeName) || 'blank' }}</span>
              </td>
              <!-- This td is only visible in smaller viewports. See CSS below. -->
              <td
                v-if="course.scheduled && size(course.scheduled)"
                :id="`td-course-${course.sectionId}-scheduled-mobile`"
                class="scheduled-mobile"
                data-label="Scheduled"
              >
                <div>
                  <span>Recordings scheduled on </span>
                  <Date :date="course.scheduled[0].createdAt" />.
                  They will be published to {{ course.scheduled[0].publishTypeName.replace('Publish to ', '') }}.
                </div>
              </td>
            </tr>
            <tr
              v-for="(meeting, meetingIndex) in tail(course.displayMeetings)"
              :id="`tr-course-${course.sectionId}-meeting-${meetingIndex + 1}`"
              :key="meetingIndex"
            >
              <td :aria-hidden="true" :colspan="showOptIn ? 3 : 2" :class="tdcLower(course)" />
              <td
                v-if="includeRoomColumn"
                :id="`td-course-${course.sectionId}-meeting-room-${get(meeting.room, 'id', 'none')}`"
                :class="tdcLower(course)"
                data-label="Room"
              >
                <router-link
                  v-if="meeting.room"
                  :id="`course-${course.sectionId}-room-${meeting.room.id}`"
                  :to="`/room/${meeting.room.id}`"
                >
                  {{ meeting.room.location }}
                </router-link>
                <span v-if="!meeting.room">&mdash;</span>
              </td>
              <td
                :id="`td-course-${course.sectionId}-meeting-room-${get(meeting.room, 'id', 'none')}-days-of-week`"
                :class="tdcLower(course)"
                data-label="Days"
              >
                <Days v-if="meeting.daysNames.length" :names-of-days="meeting.daysNames" />
                <span v-if="!meeting.daysNames.length">&mdash;</span>
              </td>
              <td
                :id="`td-course-${course.sectionId}-meeting-room-${get(meeting.room, 'id', 'none')}-dates`"
                :class="tdcLower(course)"
                data-label="Time"
              >
                <div v-if="course.nonstandardMeetingDates">
                  <Date :date="meeting.startDate" />
                  <span :aria-hidden="true"> - </span>
                  <span class="sr-only"> to </span>
                  <Date :date="meeting.endDate" />
                </div>
                <div :class="{'pb-2': course.nonstandardMeetingDates && meetingIndex === course.displayMeetings.length - 1}">
                  <span aria-hidden="true">{{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}</span>
                  <span class="sr-only">{{ meeting.startTimeFormatted }} to {{ meeting.endTimeFormatted }}</span>
                </div>
              </td>
              <td :aria-hidden="true" colspan="3" :class="tdcLower(course)" />
            </tr>
            <tr
              v-if="course.scheduled && size(course.scheduled)"
              :id="`tr-course-${course.sectionId}-scheduled`"
              :key="`approvals-${course.sectionId}`"
            >
              <td
                :id="`td-course-${course.sectionId}-scheduled-date`"
                :colspan="headers.length"
              >
                <div>
                  <span>Recordings scheduled on </span>
                  <Date :date="course.scheduled[0].createdAt" />.
                  They will be published to {{ course.scheduled[0].publishTypeName.replace('Publish to ', '') }}.
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
            v-model="page"
            :length="pageCount"
          />
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts" setup>
import type {PropType} from 'vue'
import {each, filter, find, get, map, size, tail} from 'lodash'
import {mdiClose} from '@mdi/js'
import {nextTick, onMounted, ref, watch} from 'vue'
import type {CourseSortable, SortBy} from '@/lib/types'
import {alertScreenReader, normalizeId} from '@/lib/utils'
import {getDisplayMeetings} from '@/lib/berkeley'
import {useContextStore} from '@/stores/context'
import Date from '@/components/util/Date.vue'
import Days from '@/components/util/Days.vue'
import Instructor from '@/components/course/Instructor.vue'

const props = defineProps({
  courses: {
    required: true,
    type: Array as PropType<CourseSortable[]>
  },
  description: {
    default: undefined,
    type: String
  },
  messageForCourses: {
    default: undefined,
    type: String
  },
  includeOptInColumnForUids: {
    required: false,
    type: Array,
    default: undefined
  },
  includeRoomColumn: {
    required: true,
    type: Boolean
  },
  refreshing: {
    required: true,
    type: Boolean
  },
  searchText: {
    default: undefined,
    type: String
  },
  showOptIn: {
    required: true,
    type: Boolean
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
  {key: 'instructors', title: 'Instructor(s)', screenreaderTitle: 'Instructors', value: 'instructorNames', sortable: false},
  {key: 'publish', title: 'Publish', sortable: true, value: 'publishTypeName', class: 'w-10'}
])
const page = defineModel('page', {type: Number})
const sortBy = defineModel(
  'sortBy',
  {
    default: {},
    type: Object as PropType<SortBy>
  },
)

const selectedRows = ref([])

onMounted(() => {
  if (props.showOptIn) {
    headers.value.unshift({key: 'optIn', title: 'Opt In Status', value: 'hasOptedIn', sortable: false})
  }
  if (!props.includeRoomColumn) {
    headers.value = filter(headers.value, h => h.title !== 'Room')
  }
  if (!props.showOptIn) {
    headers.value = filter(headers.value, h => h.title !== 'Opt In')
  }
  refresh()
})

const onUpdateSortBy = (primarySortBy:SortBy) => {
  const key = primarySortBy[0].key
  const header = find(headers.value, {key: key})
  sortBy.value = primarySortBy[0]
  page.value = 1
  if (header) {
    nextTick(() => alertScreenReader(`Sorted by ${header.title}, ${sortBy.value.order}ending`))
  }
}

const getOptInStatus = (course) => {
  let status = 'Not Opted In'
  if (course.hasOptedIn) {
    status = 'Opted In'
  } else {
    each(course.instructors, instructor => {
      if (!instructor.deletedAt && instructor.hasOptedIn) {
        status = 'Partial Opt-in'
        return false
      }
    })
  }
  return status
}

const refresh = () => {
  each(props.courses, course => {
    course.instructorNames = map(course.instructors, 'name')
    course.isSelectable = course.hasOptedIn
    const meetings = getDisplayMeetings(course)
    course.displayMeetings = meetings
    course.room = meetings.length && meetings[0].room ? meetings[0].room : undefined
    course.statusLabel = course.deletedAt
      ? 'Canceled'
      : (course.scheduled
        ? 'Scheduled'
        : (get(course, 'meetings.eligible.length', 0) > 0 ? 'Not Scheduled' : 'Not Eligible'))
  })
}

watch(() => props.courses, refresh)

const tdc = course => {
  return {
    'border-b-0': getDisplayMeetings(course).length > 1 || course.scheduled,
    'pt-3 pb-3': size(course.courseCodes) > 1
  }
}

const tdcLower = course => {
  return {
    'border-b-0': course.scheduled
  }
}
</script>

<style scoped>
.canceled-indicator {
  margin-left: -18px;
}

#courses-data-table td.scheduled-mobile {
  display: none;
}



@media (max-width: 1062px) {
  #courses-data-table :deep(thead),
  #courses-data-table :deep(colgroup) {
    display: none !important;
  }

  #courses-data-table,
  #courses-data-table :deep(table),
  #courses-data-table :deep(tbody),
  #courses-data-table tr,
  #courses-data-table td,
  #courses-data-table th {
    display: block;
    width: 100%;
  }

  #courses-data-table :deep(tbody > tr) {
    margin: 0 0 12px 0;
    padding: 12px;
    border: 1px solid rgba(0,0,0,0.16);
    border-radius: 12px;
    background: var(--v-theme-surface, #fff);
  }

  #courses-data-table :deep(.v-data-table__td),
  #courses-data-table :deep(.v-data-table__th),
  #courses-data-table :deep(table tr:not(:last-child) > td:not(.border-b-0)),
  #courses-data-table :deep(table tr > th) {
    border-bottom: 0 !important;
    border-top: 0 !important;
  }

  #courses-data-table :deep(tbody tr > td[aria-hidden="true"]) {
    display: none;
  }

  #courses-data-table td {
    position: relative;
    border: 0 !important;
    padding: 3px 12px;
    white-space: normal;
  }

  #courses-data-table :deep(td)::before {
    content: attr(data-label);
    display: block;
    font-weight: 600;
    opacity: 0.8;
    margin-bottom: 4px;
  }

  #courses-data-table :deep(tbody tr > td + td) { padding-top: 5px; }
  #courses-data-table :deep(tbody tr > td + td)::after {
    content: "";
    position: absolute;
    left: 12px;
    right: 12px;
    top: 0;
    height: 1px;
    background: rgba(0, 0, 0, 0.16);
    pointer-events: none;
  }

  #courses-data-table :deep(tbody tr > td[aria-hidden="true"] + td)::after {
    display: none;
  }

  #courses-data-table :deep(td[id^="td-course-"][id$="-instructors"] > div:first-child) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px 10px;
  }


  #courses-data-table :deep(td[id^="td-course-"][id$="-instructors"] > div:first-child > div) {
    display: inline-flex;
    margin: 0 !important;
    width: auto;
  }

  #courses-data-table :deep(td.scheduled-mobile) {
    display: block;
    position: relative;
    padding: 10px 12px;
    text-align: left;
  }

  /* For smaller viewports (under 1062px), we want to hide the separate scheduled row so it doesn't make its own section
     We display it in the selector above. This is why we have 2 td sections for the scheduled section. One is for larger viewports and one is for narrow viewports.*/
  #courses-data-table :deep(tr[id^="tr-course-"][id$="-scheduled"]) {
    display: none !important;
  }

  #courses-data-table {
    --v-table-row-height: auto !important;
    --v-table-header-height: auto !important;
  }

  #courses-data-table :deep(.v-table),
  #courses-data-table :deep(.v-data-table),
  #courses-data-table :deep(table) {
    --v-table-row-height: auto !important;
    --v-table-header-height: auto !important;
  }

  #courses-data-table :deep(.v-data-table__tr),
  #courses-data-table :deep(tbody > tr) {
    height: auto !important;
  }

  #courses-data-table :deep(.v-data-table__td),
  #courses-data-table :deep(.v-data-table__th) {
    min-height: 0 !important;
    height: auto !important;
    white-space: normal !important;
    word-break: break-word;
    line-height: 1.4;
    vertical-align: top;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  #courses-data-table :deep(.v-btn),
  #courses-data-table :deep(.v-chip) {
    white-space: normal !important;
    min-height: 0 !important;
    height: auto !important;
    line-height: 1.2;
    padding-top: 0;
    padding-bottom: 0;
  }

  #courses-data-table :deep(tbody > tr[id^="tr-course-"]:not([id*="-meeting-"])) {
    margin: 0 0 12px 0;
    padding: 12px;
    border: 1px solid rgba(0,0,0,0.16);
    border-radius: 12px;
    background: var(--v-theme-surface, #fff);
  }

  #courses-data-table :deep(
    tbody > tr[id^="tr-course-"]:not([id*="-meeting-"]):has(+ tr[id*="-meeting-"])
  ) {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    margin-bottom: 0;
    padding-bottom: 0;
  }

  #courses-data-table :deep(tbody > tr[id^="tr-course-"][id*="-meeting-"]) {
    margin: 0;
    border: 0;
    border-radius: 0;
    background: var(--v-theme-surface, #fff);

    padding: 10px 12px 12px;
    border-top: 1px solid rgba(0,0,0,0.16);
  }

  #courses-data-table :deep(
    tbody > tr[id^="tr-course-"][id*="-meeting-"]:not(:has(+ tr[id*="-meeting-"]))
  ) {
    border-left: 1px solid rgba(0,0,0,0.16);
    border-right: 1px solid rgba(0,0,0,0.16);
    border-bottom: 1px solid rgba(0,0,0,0.16);
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    margin-bottom: 12px;
  }

  #courses-data-table :deep(tbody > tr[id^="tr-course-"][id*="-meeting-"] td) {
    white-space: normal !important;
    word-break: break-word;
    line-height: 1.4;
    padding-top: 8px;
    padding-bottom: 8px;
  }
}
</style>
