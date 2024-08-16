<template>
  <div>
    <div v-if="courses.length && !searchText && !refreshing" id="courses-data-table-message" class="pb-1 pl-5">
      {{ messageForCourses }}
    </div>
    <v-data-table
      id="courses-data-table"
      v-model="selectedRows"
      :disable-sort="courses.length < 2"
      :headers="headers"
      hide-default-footer
      item-key="sectionId"
      :items="courses"
      :loading="refreshing"
      :must-sort="true"
      :options="{
        itemsPerPage: $config.searchItemsPerPage
      }"
      :page.sync="pageCurrent"
      :search="searchText"
      @page-count="pageCount = $event"
    >
      <template #body="{items}">
        <tbody v-if="refreshing">
          <tr>
            <td class="pa-12 text-center" :colspan="headers.length + 1">
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
        </tbody>
        <tbody v-if="!refreshing && items.length">
          <template v-for="course in items">
            <tr :key="course.sectionId">
              <td :id="`course-name-${course.sectionId}`" :class="tdc(course)">
                <div v-for="(courseCode, index) in course.courseCodes" :key="courseCode">
                  <router-link
                    v-if="index === 0"
                    :id="`link-course-${course.sectionId}`"
                    class="subtitle-1"
                    :to="`/course/${$config.currentTermId}/${course.sectionId}`"
                  >
                    <span :class="{'line-through': course.deletedAt}">{{ courseCode }}</span>
                  </router-link>
                  <span v-if="index > 0" class="subtitle-1">{{ courseCode }}</span>
                </div>
              </td>
              <td :id="`section-id-${course.sectionId}`" :class="tdc(course)">{{ course.sectionId }}</td>
              <td v-if="includeRoomColumn" :class="tdc(course)">
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
                <span v-if="!course.room && !course.room.location">&mdash;</span>
              </td>
              <td :id="`meeting-days-${course.sectionId}-0`" :class="tdc(course)">
                <div :class="{'line-through': course.deletedAt}">
                  <Days v-if="course.displayMeetings[0].daysNames.length" :names-of-days="course.displayMeetings[0].daysNames" />
                  <span v-if="!course.displayMeetings[0].daysNames.length">&mdash;</span>
                </div>
              </td>
              <td :id="`meeting-times-${course.sectionId}-0`" :class="tdc(course)">
                <div :class="{'line-through': course.deletedAt}">
                  <div v-if="course.nonstandardMeetingDates">
                    <span class="text-no-wrap">{{ course.displayMeetings[0].startDate | moment('MMM D, YYYY') }} - </span>
                    <span class="text-no-wrap">{{ course.displayMeetings[0].endDate | moment('MMM D, YYYY') }}</span>
                  </div>
                  <span class="text-no-wrap">{{ course.displayMeetings[0].startTimeFormatted }} - {{ course.displayMeetings[0].endTimeFormatted }}</span>
                </div>
              </td>
              <td :id="`course-${course.sectionId}-status`" :class="tdc(course)">
                <div v-if="course.deletedAt">
                  <v-icon
                    color="red"
                    class="font-weight-bold pb-1 pl-0"
                    v-bind="attrs"
                    v-on="on"
                  >
                    mdi-close
                  </v-icon>
                  <span class="font-weight-bold red--text">Canceled</span>
                </div>
                <div v-if="!course.deletedAt && course.scheduled">
                  Scheduled
                </div>
                <div v-if="!course.deletedAt && !course.scheduled">
                  Not Scheduled
                </div>
              </td>
              <td :class="tdc(course)">
                <div v-if="course.instructors.length">
                  <div v-for="instructor in course.instructors" :key="instructor.uid" class="mb-1 mt-1">
                    <Instructor :course="course" :instructor="instructor" />
                  </div>
                </div>
                <div v-if="!course.instructors.length">
                  &mdash;
                </div>
              </td>
              <td :id="`course-${course.sectionId}-publish-types`" :class="tdc(course)">
                {{ course.publishTypeName || '&mdash;' }}
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
            <tr v-for="index in $_.size(course.displayMeetings) - 1" :key="`${course.sectionId}-${index}`">
              <td colspan="2" :class="tdcLower(course)"></td>
              <td v-if="includeRoomColumn" :class="tdcLower(course)">
                <router-link
                  v-if="course.displayMeetings[index].room"
                  :id="`course-${course.sectionId}-room-${course.displayMeetings[index].room.id}`"
                  :to="`/room/${course.displayMeetings[index].room.id}`"
                >
                  {{ course.displayMeetings[index].room.location }}
                </router-link>
                <span v-if="!course.displayMeetings[index].room">&mdash;</span>
              </td>
              <td class="text-no-wrap" :class="tdcLower(course)">
                <Days v-if="course.displayMeetings[index].daysNames.length" :names-of-days="course.displayMeetings[index].daysNames" />
                <span v-if="!course.displayMeetings[index].daysNames.length">&mdash;</span>
              </td>
              <td class="text-no-wrap" :class="tdcLower(course)">
                <div v-if="course.nonstandardMeetingDates">
                  <span class="text-no-wrap">{{ course.displayMeetings[index].startDate | moment('MMM D, YYYY') }} - </span>
                  <span class="text-no-wrap">{{ course.displayMeetings[index].endDate | moment('MMM D, YYYY') }}</span>
                </div>
                <div :class="{'pb-2': course.nonstandardMeetingDates && index === course.displayMeetings.length - 1}">
                  {{ course.displayMeetings[index].startTimeFormatted }} - {{ course.displayMeetings[index].endTimeFormatted }}
                </div>
              </td>
              <td colspan="4" :class="tdcLower(course)"></td>
            </tr>
            <tr v-if="course.scheduled" :key="`approvals-${course.sectionId}`">
              <td :colspan="headers.length + 1" class="pb-2">
                <div v-if="course.scheduled" class="pb-3">
                  Recordings scheduled on {{ course.scheduled[0].createdAt | moment('MMM D, YYYY') }}.
                  They will be published to {{ course.scheduled[0].publishTypeName.replace('Publish to ', '') }}.
                </div>
              </td>
              <td></td>
            </tr>
          </template>
        </tbody>
        <tbody v-if="!refreshing && !items.length">
          <tr>
            <td id="message-when-zero-courses" class="pa-4 text-no-wrap title" :colspan="headers.length">
              <span v-if="!refreshing">No courses.</span>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
    <div v-if="!refreshing && pageCount > 1" class="text-center pb-4 pt-2">
      <v-pagination
        id="ouija-pagination"
        v-model="pageCurrent"
        :length="pageCount"
        total-visible="10"
      ></v-pagination>
    </div>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import Days from '@/components/util/Days'
import Instructor from '@/components/course/Instructor'
import ToggleOptOut from '@/components/course/ToggleOptOut'
import Utils from '@/mixins/Utils'

export default {
  name: 'CoursesDataTable',
  components: {Days, Instructor, ToggleOptOut},
  mixins: [Context, Utils],
  props: {
    courses: {
      required: true,
      type: Array
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
    messageForCourses: {
      default: undefined,
      type: String
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
    },
  },
  data: () => ({
    headers: [
      {text: 'Course', value: 'label'},
      {text: 'Section', value: 'sectionId', class: 'w-10'},
      {text: 'Room', value: 'room.location'},
      {text: 'Days', sortable: false},
      {text: 'Time', sortable: false},
      {text: 'Status', class: 'w-10', sortable: false},
      {text: 'Instructor(s)', value: 'instructorNames', sortable: false},
      {text: 'Publish', value: 'publishTypeName', class: 'w-10'},
      {text: 'Opt out', value: 'hasOptedOut', sortable: false}
    ],
    pageCount: undefined,
    pageCurrent: 1,
    selectedRows: [],
    selectedFilter: 'Scheduled'
  }),
  watch: {
    refreshing(value) {
      if (!value) {
        // False value means that the refresh just ended in the parent component and we can proceed.
        this.refresh()
      }
    }
  },
  created() {
    this.refresh()
  },
  methods: {
    refresh() {
      this.pageCurrent = 1
      if (!this.includeRoomColumn) {
        this.headers = this.$_.filter(this.headers, h => h.text !== 'Room')
      }
      if (!this.includeOptOutColumnForUid) {
        this.headers = this.$_.filter(this.headers, h => h.text !== 'Opt out')
      }
      this.$_.each(this.courses, course => {
        course.instructorNames = this.$_.map(course.instructors, 'name')
        course.isSelectable = !course.hasOptedOut
        const meetings = this.getDisplayMeetings(course)
        course.displayMeetings = meetings
        course.room = meetings.length && meetings[0].room ? meetings[0].room : null
      })
    },
    tdc(course) {
      return {
        'border-bottom-zero': this.getDisplayMeetings(course).length > 1 || course.scheduled,
        'pt-3 pb-3': this.$_.size(course.courseCodes) > 1
      }
    },
    tdcLower(course) {
      return {
        'border-bottom-zero': course.scheduled
      }
    }
  }
}
</script>
