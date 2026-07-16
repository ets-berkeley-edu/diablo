<template>
  <v-data-table
    class="instructor-courses overflow-y-visible"
    disable-sort
    :headers="[
      {title: 'Status', value: 'status'},
      {title: 'Course', value: 'label'},
      {title: 'Title', value: 'title'},
      {title: 'Instructors', value: 'instructors'},
      {title: 'Room', value: 'room'},
      {title: 'Days', value: 'days'},
      {title: 'Time', value: 'time'}
    ]"
    hide-default-footer
    :items="courses"
    :items-per-page="-1"
  >
    <template #headers="{columns}">
      <tr>
        <th
          v-for="(column, index) in columns"
          :id="`${idPrefix}-${column.value}-th`"
          :key="index"
          class="text-start"
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
          :id="`${idPrefix}-${course.sectionId}`"
          class="course-row"
          tabindex="0"
        >
          <td
            :id="`course-${course.sectionId}-status`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Status"
          >
            <div v-if="course.statusLabel === 'Canceled'" class="canceled-indicator d-flex">
              <v-icon color="error" :icon="mdiClose" />
              <span class="font-weight-bold text-error">{{ course.statusLabel }}</span>
            </div>
            <div v-else>
              <v-tooltip
                :text="describeRecordingsStatus(course.statusLabel)"
                location="top"
              >
                <template #activator="{ props: activatorProps }">
                  <span v-bind="activatorProps">{{ course.statusLabel }}</span>
                </template>
              </v-tooltip>
            </div>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-label`"
            :aria-rowspan="size(course.displayMeetings)"
            :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Course"
          >
            <div v-for="(courseCode, index) in course.courseCodes" :key="courseCode">
              <router-link
                v-if="index === 0"
                :id="`link-course-${course.sectionId}`"
                class="course-link"
                :to="`/course/${config.currentTermId}/${course.sectionId}`"
              >
                {{ courseCode }}
              </router-link>
              <span v-if="index > 0">{{ courseCode }}</span>
            </div>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-title`"
            :aria-rowspan="size(course.displayMeetings)"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Title"
          >
            <span aria-hidden="true">{{ course.courseTitle || '&mdash;' }}</span>
            <span class="sr-only">{{ course.courseTitle || 'blank' }}</span>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-instructors`"
            :aria-rowspan="size(course.displayMeetings)"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Instructors"
          >
            {{ oxfordJoin(map(course.instructors, 'name')) }}
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-room-0`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Room"
          >
            {{ course.displayMeetings[0].room.location }}
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-days-0`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Days"
          >
            <Days v-if="size(course.displayMeetings[0].daysNames)" :names-of-days="course.displayMeetings[0].daysNames" />
            <span v-if="isEmpty(course.displayMeetings[0].daysNames)">&mdash;</span>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-time-0`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            data-label="Time"
          >
            <div v-if="course.nonstandardMeetingDates" class="pt-2">
              <span>
                {{ DateTime.fromISO(course.displayMeetings[0].startDate).toFormat('MMM d, yyyy') }} -
              </span>
              <span>
                {{ DateTime.fromISO(course.displayMeetings[0].endDate).toFormat('MMM d, yyyy') }}
              </span>
            </div>
            <span aria-hidden="true">{{ course.displayMeetings[0].startTimeFormatted }} - {{ course.displayMeetings[0].endTimeFormatted }}</span>
            <span class="sr-only">{{ course.displayMeetings[0].startTimeFormatted }} to {{ course.displayMeetings[0].endTimeFormatted }}</span>
          </td>
        </tr>
        <tr
          v-for="(meeting, index) in tail<Meeting[]>(course.displayMeetings)"
          :id="`${idPrefix}-${course.sectionId}-${index}`"
          :key="`${course.sectionId}-${index}`"
          class="meeting-row"
          tabindex="0"
        >
          <td :aria-hidden="true" colspan="4" />
          <td
            :id="`${idPrefix}-${course.sectionId}-room-${index + 1}`"
            class="pt-0"
            data-label="Room"
          >
            {{ meeting.room.location }}
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-days-${index + 1}`"
            data-label="Days"
          >
            <Days :names-of-days="meeting.daysNames" />
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-time-${index + 1}`"
            data-label="Dates"
          >
            <div v-if="course.nonstandardMeetingDates" class="pt-2">
              <span>
                {{ DateTime.fromISO(meeting.startDate).toFormat('MMM d, yyyy') }} -
              </span>
              <span>
                {{ DateTime.fromISO(meeting.endDate).toFormat('MMM d, yyyy') }}
              </span>
            </div>
            <div :class="{'pb-2': course.nonstandardMeetingDates && index === (size(course.displayMeetings) - 1)}">
              {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
            </div>
          </td>
        </tr>
      </template>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import type {PropType} from 'vue'
import {isEmpty, map, size, tail} from 'lodash'
import {DateTime} from 'luxon'
import {mdiClose} from '@mdi/js'
import type {Course, Meeting} from '@/lib/types'
import {oxfordJoin} from '@/lib/utils'
import Days from '@/components/util/Days.vue'
import {describeRecordingsStatus} from '@/lib/berkeley'
import {useContextStore} from '@/stores/context'

const props = defineProps({
  courses: {
    required: true,
    type: Array as PropType<Course[]>
  },
  coursesType: {
    required: true,
    type: String,
    validator: (value: string) => ['eligible', 'ineligible'].includes(value)
  }
})

const config = useContextStore().config
const idPrefix = `courses-table-${props.coursesType}`
</script>

<style scoped>
.course-link {
  text-decoration: underline !important;
  text-underline-offset: 2px;
  cursor: pointer;
}

/* For smaller viewports. 941px is the magic number here because that is when the horizontal scrollbar appears.
 * We stack all the rows on top of each other as individual cards.
 * Somewhat similar to BOA and a student's course progress.
*/
@media (max-width: 941px) {
  .instructor-courses :deep(thead) {
    display: none !important;
  }

  .instructor-courses :deep(colgroup) {
    display: none;
  }

  .instructor-courses :deep(table),
  .instructor-courses :deep(tbody),
  .instructor-courses tr,
  .instructor-courses td,
  .instructor-courses th {
    display: block;
    width: 100%;
  }

  .instructor-courses tbody tr {
    margin: 0 0 12px 0;
    padding: 12px;
    border: 1px solid var(--v-theme-outline-variant, rgba(0,0,0,0.12));
    border-radius: 12px;
    box-shadow: var(--v-shadow-1);
    background: var(--v-theme-surface, #fff);
  }

  .instructor-courses td {
    border: none !important;
    padding: 10px 12px;
    white-space: normal;
  }

  .instructor-courses td::before {
    content: attr(data-label);
    display: block;
    font-weight: 600;
    opacity: 0.8;
    margin-bottom: 4px;
  }

  .instructor-courses tbody tr > td[aria-hidden="true"] {
    display: none;
  }

  .instructor-courses tbody tr > td:not([aria-hidden]) {
    border-top: thin solid rgb(var(--v-theme-table-border)) !important;
    padding-top: 3px;
  }

  .instructor-courses tbody tr > td:first-child {
    border-top: none !important;
  }
  .instructor-courses tbody tr > td[aria-hidden="true"] + td {
    border-top: none !important;
  }

  .instructor-courses :deep(table tr:not(:last-child) > td:not(.border-b-0)),
  .instructor-courses :deep(table tr > th) {
    border-bottom: 0 !important;
    padding-top: 3px;
  }

  .instructor-courses :deep(.v-data-table__td),
  .instructor-courses :deep(.v-data-table__th) {
    border-bottom: 0 !important;
  }

  .instructor-courses {
  --v-table-row-height: auto !important;
  --v-table-header-height: auto !important;
  }
  .instructor-courses :deep(.v-table),
  .instructor-courses :deep(.v-data-table),
  .instructor-courses :deep(table) {
    --v-table-row-height: auto !important;
    --v-table-header-height: auto !important;
  }
  .instructor-courses :deep(.v-data-table__tr),
  .instructor-courses :deep(tbody > tr) {
    height: auto !important;
  }
  .instructor-courses :deep(.v-data-table__td),
  .instructor-courses :deep(.v-data-table__th) {
    min-height: 0 !important;
    height: auto !important;
    white-space: normal !important;
    word-break: break-word;
    line-height: 1.4;
  }

  .instructor-courses tbody tr.course-row {
    margin: 0 0 12px 0;
    padding: 12px;
    border: 1px solid var(--v-theme-outline-variant, rgba(0,0,0,0.12));
    border-radius: 12px;
    box-shadow: var(--v-shadow-1);
    background: var(--v-theme-surface, #fff);
  }

  .instructor-courses tbody tr.course-row + tr.meeting-row {
    margin-top: 0;
  }
  .instructor-courses tbody tr.course-row:has(+ tr.meeting-row) {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    margin-bottom: 0;
    padding-bottom: 0;
  }

  .instructor-courses tbody tr.meeting-row {
    display: block;
    margin: 0;
    border: 0;
    border-radius: 0;
    background: var(--v-theme-surface, #fff);
    padding: 10px 12px 12px;
    border-top: 1px solid var(--v-theme-outline-variant, rgba(0,0,0,0.12));
  }

  .instructor-courses tbody tr.meeting-row:not(:has(+ tr.meeting-row)) {
    border-left: 1px solid var(--v-theme-outline-variant, rgba(0,0,0,0.12));
    border-right: 1px solid var(--v-theme-outline-variant, rgba(0,0,0,0.12));
    border-bottom: 1px solid var(--v-theme-outline-variant, rgba(0,0,0,0.12));
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    margin-bottom: 12px;
  }

  .instructor-courses tbody tr.meeting-row > td {
    padding-top: 8px;
    padding-bottom: 8px;
    border-top: none !important;
  }

    .instructor-courses tbody tr > td {
      border-top: none !important;
    }

  .instructor-courses tbody tr.meeting-row > td {
    position: relative;
  }

  .instructor-courses tbody tr.meeting-row > td + td::after {
    content: "";
    position: absolute;
    left: 12px;
    right: 12px;
    top: 0;
    height: 1px;
    background: rgba(0, 0, 0, 0.16);
    pointer-events: none;
  }

  .instructor-courses tbody tr.meeting-row > td:first-of-type::after,
  .instructor-courses tbody tr.meeting-row > td[aria-hidden="true"] + td::after {
    display: none;
  }
}


</style>
