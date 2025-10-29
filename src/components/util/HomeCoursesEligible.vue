<template>
  <div
    aria-labelledby="courses-table-eligible-header"
    role="region"
  >
    <h2 id="courses-table-eligible-header" class="pt-4 px-4 text-medium-emphasis w-100">
      Courses eligible for capture
    </h2>
    <div class="overflow-x-auto px-md-4 w-100">
      <div v-if="isEmpty(courses)" class="px-4 pt-2">No courses.</div>
      <v-data-table
        v-if="size(courses)"
        id="courses-table-eligible"
        class="instructor-courses overflow-y-visible"
        disable-sort
        :headers="headers"
        hide-default-footer
        :items="courses"
        :items-per-page="-1"
      >
        <template #headers="{columns}">
          <tr>
            <th
              v-for="(column, colIndex) in columns"
              :id="`courses-table-eligible-${column.value}-th`"
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
              :id="`courses-table-eligible-${course.sectionId}`"
              tabindex="0"
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
                :id="`courses-table-eligible-${course.sectionId}-label`"
                :aria-rowspan="size(course.displayMeetings)"
                class="text-no-wrap"
                :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-b-0': size(course.displayMeetings) > 1}"
                :columnheader="`courses-table-eligible-label-th`"
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
                :id="`courses-table-eligible-${course.sectionId}-title`"
                :aria-rowspan="size(course.displayMeetings)"
                :class="{'border-b-0': size(course.displayMeetings) > 1}"
                :columnheader="`courses-table-eligible-title-th`"
              >
                <span aria-hidden="true">{{ course.courseTitle || '&mdash;' }}</span>
                <span class="sr-only">{{ course.courseTitle || 'blank' }}</span>
              </td>
              <td
                :id="`courses-table-eligible-${course.sectionId}-instructors`"
                :aria-rowspan="size(course.displayMeetings)"
                :class="{'border-b-0': size(course.displayMeetings) > 1}"
                :columnheader="`courses-table-eligible-instructors-th`"
              >
                {{ oxfordJoin(map(course.instructors, 'name')) }}
              </td>
              <td
                :id="`courses-table-eligible-${course.sectionId}-room-0`"
                :class="{'border-b-0': size(course.displayMeetings) > 1}"
                :columnheader="`courses-table-eligible-room-th`"
              >
                {{ course.displayMeetings[0].room.location }}
              </td>
              <td
                :id="`courses-table-eligible-${course.sectionId}-days-0`"
                :class="{'border-b-0': size(course.displayMeetings) > 1}"
                class="text-no-wrap"
                :columnheader="`courses-table-eligible-days-th`"
              >
                <Days v-if="size(course.displayMeetings[0].daysNames)" :names-of-days="course.displayMeetings[0].daysNames" />
                <span v-if="isEmpty(course.displayMeetings[0].daysNames)">&mdash;</span>
              </td>
              <td
                :id="`courses-table-eligible-${course.sectionId}-time-0`"
                :class="{'border-b-0': size(course.displayMeetings) > 1}"
                :columnheader="`courses-table-eligible-time-th`"
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
              :id="`courses-table-eligible-${course.sectionId}-${meetingIndex}`"
              :key="`${course.sectionId}-${meetingIndex}`"
              tabindex="0"
            >
              <td :aria-hidden="true" colspan="4" />
              <td
                :id="`courses-table-eligible-${course.sectionId}-room-${meetingIndex + 1}`"
                class="pt-0 text-no-wrap"
                :columnheader="`courses-table-eligible-room-th`"
              >
                {{ meeting.room.location }}
              </td>
              <td
                :id="`courses-table-eligible-${course.sectionId}-days-${meetingIndex + 1}`"
                class="text-no-wrap"
                :columnheader="`courses-table-eligible-days-th`"
              >
                <Days :names-of-days="meeting.daysNames" />
              </td>
              <td
                :id="`courses-table-eligible-${course.sectionId}-time-${meetingIndex + 1}`"
                class="text-no-wrap"
                :columnheader="`courses-table-eligible-time-th`"
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
              <td :aria-hidden="true" />
            </tr>
          </template>
        </template>
      </v-data-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type {PropType} from 'vue'
import {isEmpty, map, size, tail} from 'lodash'
import {DateTime} from 'luxon'
import {mdiClose} from '@mdi/js'
import type {Course} from '@/lib/types'
import {oxfordJoin} from '@/lib/utils'
import Days from '@/components/util/Days.vue'
import {describeRecordingsStatus} from '@/lib/berkeley'
import {useContextStore} from '@/stores/context'

defineProps({
  courses: {
    required: true,
    type: Array as PropType<Course[]>
  }
})

const config = useContextStore().config
const headers = [
  {title: 'Status', value: 'status'},
  {title: 'Course', value: 'label'},
  {title: 'Title', value: 'title'},
  {title: 'Instructors', value: 'instructors'},
  {title: 'Room', value: 'room'},
  {title: 'Days', value: 'days'},
  {title: 'Time', value: 'time'},
]
</script>

<style scoped>
.course-link {
  text-decoration: underline !important;
  text-underline-offset: 2px;
  cursor: pointer;
}
</style>
