<template>
  <div aria-describedby="courses-data-table-message" aria-label="Courses table" role="region">
    <v-row id="courses-data-table-message" class="text-medium-emphasis pb-1 px-4">
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
              <span class="font-size-13 font-weight-bold py-1 text-align-center text-medium-emphasis text-transform-unset v-btn" :class="{'opacity-30': refreshing}">
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
            <tr>
              <td v-if="showOptIn && course.statusLabel !== 'Not Eligible'" :class="tdc(course)">
                <span>
                  {{ course.hasOptedIn ? 'Opted In' : 'Not Opted In' }}
                </span>
              </td>
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
                  <div v-if="course.nonstandardMeetingDates && get(course, 'displayMeetings.0.startDate') && get(course, 'displayMeetings.0.endDate')">
                    <Date class="text-no-wrap" :date="course.displayMeetings[0].startDate" />
                    <span :aria-hidden="true"> - </span>
                    <span class="sr-only"> to </span>
                    <Date class="text-no-wrap" :date="course.displayMeetings[0].endDate" />
                  </div>
                  <span aria-hidden="true" class="text-no-wrap">{{ get(course, 'displayMeetings.0.startTimeFormatted') }} - {{ get(course, 'displayMeetings.0.endTimeFormatted') }}</span>
                  <span class="sr-only">{{ get(course, 'displayMeetings.0.startTimeFormatted') }} to {{ get(course, 'displayMeetings.0.endTimeFormatted') }}</span>
                </div>
              </td>
              <td :id="`course-${course.sectionId}-status`" :class="tdc(course)" columnheader="courses-table-status-th">
                <div v-if="course.statusLabel === 'Canceled'" class="canceled-indicator d-flex">
                  <v-icon color="error" :icon="mdiClose" />
                  <span class="font-weight-bold text-error">{{ course.statusLabel }}</span>
                </div>
                <div v-else>
                  {{ course.statusLabel }}
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
            </tr>
            <tr v-for="(meeting, meetingIndex) in tail(course.displayMeetings)" :key="`${course.sectionId}-${meetingIndex}`">
              <td :aria-hidden="true" colspan="2" :class="tdcLower(course)" />
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
                  <Date class="text-no-wrap" :date="meeting.startDate" />
                  <span :aria-hidden="true"> - </span>
                  <span class="sr-only"> to </span>
                  <Date class="text-no-wrap" :date="meeting.endDate" />
                </div>
                <div :class="{'pb-2': course.nonstandardMeetingDates && meetingIndex === course.displayMeetings.length - 1}">
                  <span aria-hidden="true">{{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}</span>
                  <span class="sr-only">{{ meeting.startTimeFormatted }} to {{ meeting.endTimeFormatted }}</span>
                </div>
              </td>
              <td :aria-hidden="true" colspan="3" :class="tdcLower(course)" />
            </tr>
            <tr v-if="course.scheduled && size(course.scheduled)" :key="`approvals-${course.sectionId}`">
              <td :colspan="headers.length" class="pb-2">
                <div class="pb-3">
                  <span>Recordings scheduled on </span>
                  <Date class="text-no-wrap" :date="course.scheduled[0].createdAt" />.
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
import {onMounted, ref} from 'vue'
import type {CourseSortable, SortBy} from '@/lib/types'
import {alertScreenReader} from '@/lib/utils'
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
  onToggleOptIn: {
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
  },
  showOptIn: {
    required: true,
    type: Boolean
  }
})

const contextStore = useContextStore()
const headers = ref([
  {key: 'optIn', title: 'Opt In Status', value: 'hasOptedIn', sortable: false},
  {key: 'course', title: 'Course', sortable: true, value: 'label'},
  {key: 'section', title: 'Section', sortable: true, value: 'sectionId', class: 'w-10'},
  {key: 'room', title: 'Room', sortable: true, value: 'room.location'},
  {key: 'days', title: 'Days', sortable: false},
  {key: 'time', title: 'Time', sortable: false},
  {key: 'status', title: 'Status', class: 'w-10', sortable: false},
  {key: 'instructors', title: 'Instructor(s)', value: 'instructorNames', sortable: false},
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
    alertScreenReader(`Sorted by ${header.title}, ${sortBy.value.order}ending`)
  }
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
</style>
