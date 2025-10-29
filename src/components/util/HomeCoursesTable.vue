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
          :id="`${idPrefix}-${course.sectionId}`"
          tabindex="0"
        >
          <td
            :id="`course-${course.sectionId}-status`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
          >
            <div v-if="course.statusLabel === 'Canceled'" class="canceled-indicator d-flex">
              <v-icon color="error" :icon="mdiClose" />
              <span class="font-weight-bold text-no-wrap text-error">{{ course.statusLabel }}</span>
            </div>
            <div v-else>
              <v-tooltip
                :text="describeRecordingsStatus(course.statusLabel)"
                location="top"
              >
                <template #activator="{ props }">
                  <span v-bind="props" class="text-no-wrap">{{ course.statusLabel }}</span>
                </template>
              </v-tooltip>
            </div>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-label`"
            :aria-rowspan="size(course.displayMeetings)"
            class="text-no-wrap"
            :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-b-0': size(course.displayMeetings) > 1}"
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
          >
            <span aria-hidden="true">{{ course.courseTitle || '&mdash;' }}</span>
            <span class="sr-only">{{ course.courseTitle || 'blank' }}</span>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-instructors`"
            :aria-rowspan="size(course.displayMeetings)"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
          >
            {{ oxfordJoin(map(course.instructors, 'name')) }}
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-room-0`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
          >
            {{ course.displayMeetings[0].room.location }}
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-days-0`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
            class="text-no-wrap"
          >
            <Days v-if="size(course.displayMeetings[0].daysNames)" :names-of-days="course.displayMeetings[0].daysNames" />
            <span v-if="isEmpty(course.displayMeetings[0].daysNames)">&mdash;</span>
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-time-0`"
            :class="{'border-b-0': size(course.displayMeetings) > 1}"
          >
            <div v-if="course.nonstandardMeetingDates" class="pt-2">
              <span class="text-no-wrap">
                {{ DateTime.fromISO(course.displayMeetings[0].startDate).toFormat('MMM d, yyyy') }} -
              </span>
              <span class="text-no-wrap">
                {{ DateTime.fromISO(course.displayMeetings[0].endDate).toFormat('MMM d, yyyy') }}
              </span>
            </div>
            <span aria-hidden="true" class="text-no-wrap">{{ course.displayMeetings[0].startTimeFormatted }} - {{ course.displayMeetings[0].endTimeFormatted }}</span>
            <span class="sr-only">{{ course.displayMeetings[0].startTimeFormatted }} to {{ course.displayMeetings[0].endTimeFormatted }}</span>
          </td>
        </tr>
        <tr
          v-for="(meeting, index) in tail<Meeting[]>(course.displayMeetings)"
          :id="`${idPrefix}-${course.sectionId}-${index}`"
          :key="`${course.sectionId}-${index}`"
          tabindex="0"
        >
          <td :aria-hidden="true" colspan="4" />
          <td
            :id="`${idPrefix}-${course.sectionId}-room-${index + 1}`"
            class="pt-0 text-no-wrap"
          >
            {{ meeting.room.location }}
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-days-${index + 1}`"
            class="text-no-wrap"
          >
            <Days :names-of-days="meeting.daysNames" />
          </td>
          <td
            :id="`${idPrefix}-${course.sectionId}-time-${index + 1}`"
            class="text-no-wrap"
          >
            <div v-if="course.nonstandardMeetingDates" class="pt-2">
              <span class="text-no-wrap">
                {{ DateTime.fromISO(meeting.startDate).toFormat('MMM d, yyyy') }} -
              </span>
              <span class="text-no-wrap">
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
</style>
