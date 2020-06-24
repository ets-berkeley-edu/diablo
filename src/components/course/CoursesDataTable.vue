<template>
  <div>
    <div v-if="courses.length && !searchText && !refreshing" id="courses-data-table-message" class="pb-1 pl-5">
      {{ messageForCourses }}
    </div>
    <v-data-table
      id="courses-data-table"
      v-model="selectedRows"
      :headers="headers"
      hide-default-footer
      item-key="sectionId"
      :items="courses"
      :loading="refreshing"
      :options="{
        itemsPerPage: $config.searchItemsPerPage
      }"
      :page.sync="pageCurrent"
      :search="searchText"
      @page-count="pageCount = $event"
    >
      <template v-slot:body="{ items }">
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
                    {{ courseCode }}
                  </router-link>
                  <span v-if="index > 0" class="subtitle-1">{{ courseCode }}</span>
                </div>
              </td>
              <td :id="`section-id-${course.sectionId}`" :class="tdc(course)">{{ course.sectionId }}</td>
              <td v-if="includeRoomColumn" :class="tdc(course)">
                <div v-if="meetings(course).length && meetings(course)[0].room">
                  <router-link
                    :id="`course-${course.sectionId}-room-${meetings(course)[0].room.id}`"
                    :to="`/room/${meetings(course)[0].room.id}`"
                  >
                    {{ meetings(course)[0].room.location }}
                  </router-link>
                </div>
                <span v-if="!meetings(course).length || !meetings(course)[0].room">&mdash;</span>
              </td>
              <td :id="`meeting-days-${course.sectionId}-0`" :class="tdc(course)">
                {{ $_.join(meetings(course)[0].daysFormatted, ', ') || '&mdash;' }}
              </td>
              <td :id="`meeting-times-${course.sectionId}-0`" :class="tdc(course)">
                <div v-if="course.nonstandardMeetingDates">
                  <span class="text-no-wrap">{{ meetings(course)[0].startDate | moment('MMM D, YYYY') }} - </span>
                  <span class="text-no-wrap">{{ meetings(course)[0].endDate | moment('MMM D, YYYY') }}</span>
                </div>
                <span class="text-no-wrap">{{ meetings(course)[0].startTimeFormatted }} - {{ meetings(course)[0].endTimeFormatted }}</span>
              </td>
              <td :id="`course-${course.sectionId}-status`" :class="tdc(course)">
                <v-tooltip v-if="course.wasApprovedByAdmin" :id="`tooltip-admin-approval-${course.sectionId}`" bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon
                      color="green"
                      class="pa-0"
                      dark
                      v-on="on"
                    >
                      mdi-account-check-outline
                    </v-icon>
                  </template>
                  Course Capture Admin {{ $_.last(course.approvals).approvedBy.name }}
                  submitted approval on
                  {{ $_.last(course.approvals).createdAt | moment('MMM D, YYYY') }}.
                </v-tooltip>
                <div :id="`course-${course.sectionId}-approval-status`">{{ course.approvalStatus || '&mdash;' }}</div>
                <div :id="`course-${course.sectionId}-scheduling-status`">{{ course.schedulingStatus || '&mdash;' }}</div>
              </td>
              <td :class="tdc(course)">
                <div v-for="instructor in course.instructors" :key="instructor.uid" class="mb-1 mt-1">
                  <v-tooltip v-if="instructor.approval" :id="`tooltip-approval-${course.sectionId}-by-${instructor.uid}`" bottom>
                    <template v-slot:activator="{ on }">
                      <v-icon
                        :color="instructor.approval ? 'green' : 'yellow darken-2'"
                        class="pa-0"
                        dark
                        v-on="on"
                      >
                        mdi-check
                      </v-icon>
                    </template>
                    Approval submitted on {{ instructor.approval.createdAt | moment('MMM D, YYYY') }}.
                  </v-tooltip>
                  <router-link :id="`course-${course.sectionId}-instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                    {{ instructor.name }}
                  </router-link> ({{ instructor.uid }})
                </div>
              </td>
              <td :id="`course-${course.sectionId}-publish-types`" :class="tdc(course)">
                {{ course.publishTypeNames || '&mdash;' }}
              </td>
              <td :class="tdc(course)">
                <ToggleOptOut
                  v-if="!course.hasNecessaryApprovals && !course.scheduled"
                  :key="course.sectionId"
                  :course="course"
                  :on-toggle="onToggleOptOut"
                />
              </td>
            </tr>
            <tr v-for="index in meetings(course).length - 1" :key="`${course.sectionId}-${index}`">
              <td colspan="2" :class="mdc(course)"></td>
              <td v-if="includeRoomColumn" :class="mdc(course)">
                <router-link
                  v-if="meetings(course)[index].room"
                  :id="`course-${course.sectionId}-room-${meetings(course)[index].room.id}`"
                  :to="`/room/${meetings(course)[index].room.id}`"
                >
                  {{ meetings(course)[index].room.location }}
                </router-link>
                <span v-if="!meetings(course)[index].room">&mdash;</span>
              </td>
              <td class="text-no-wrap" :class="mdc(course)">
                {{ $_.join(meetings(course)[index].daysFormatted, ', ') || '&mdash;' }}
              </td>
              <td class="text-no-wrap" :class="mdc(course)">
                <div v-if="course.nonstandardMeetingDates">
                  <span class="text-no-wrap">{{ meetings(course)[index].startDate | moment('MMM D, YYYY') }} - </span>
                  <span class="text-no-wrap">{{ meetings(course)[index].endDate | moment('MMM D, YYYY') }}</span>
                </div>
                <div :class="{'pb-2': course.nonstandardMeetingDates && index === meetings(course).length - 1}">
                  {{ meetings(course)[index].startTimeFormatted }} - {{ meetings(course)[index].endTimeFormatted }}
                </div>
              </td>
              <td colspan="4" :class="mdc(course)"></td>
            </tr>
            <tr v-if="course.approvals.length" :key="`approvals-${course.sectionId}`">
              <td :colspan="headers.length + 1" class="pb-2">
                <div v-if="course.approvals.length" class="pb-3">
                  <span v-for="approval in course.approvals" :key="approval.approvedBy.uid">
                    <router-link :id="`instructor-${approval.approvedBy.uid}-mailto`" :to="`/user/${approval.approvedBy.uid}`">
                      {{ approval.approvedBy.name }}
                    </router-link> ({{ approval.approvedBy.uid }}) selected "{{ approval.recordingTypeName }}".
                  </span>
                  <span v-if="course.scheduled">
                    Recordings scheduled on {{ course.scheduled.createdAt | moment('MMM D, YYYY') }}.
                    They will be published to {{ course.scheduled.publishTypeName }}.
                  </span>
                </div>
              </td>
              <td></td>
            </tr>
          </template>
        </tbody>
        <tbody v-if="!refreshing && !items.length">
          <tr>
            <td id="message-when-zero-courses" class="ma-4 text-no-wrap title" :colspan="headers.length">
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
  import ToggleOptOut from '@/components/course/ToggleOptOut'
  import Utils from '@/mixins/Utils'

  export default {
    name: 'CoursesDataTable',
    components: {ToggleOptOut},
    mixins: [Context, Utils],
    props: {
      courses: {
        required: true,
        type: Array
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
        required: true,
        type: Function
      },
      refreshing: {
        required: true,
        type: Boolean
      },
      searchText: {
        default: undefined,
        type: String
      }
    },
    data: () => ({
      headers: [
        {text: 'Course', value: 'label'},
        {text: 'Section', value: 'sectionId', class: 'w-10'},
        {text: 'Room', value: 'room.location'},
        {text: 'Days', sortable: false},
        {text: 'Time', sortable: false},
        {text: 'Status', class: 'w-10', sortable: false},
        {text: 'Instructor(s)', value: 'instructorNames'},
        {text: 'Publish', value: 'publishTypeNames', class: 'w-10'},
        {text: 'Opt out', value: 'hasOptedOut', sortable: false}
      ],
      pageCount: undefined,
      pageCurrent: 1,
      selectedRows: [],
      selectedFilter: 'Not Invited'
    }),
    watch: {
      refreshing(isRefreshing) {
        if (isRefreshing) {
          this.pageCurrent = 1
        }
      }
    },
    mounted() {
      this.headers = this.includeRoomColumn ? this.headers : this.$_.filter(this.headers, h => h.text !== 'Room')
      this.$_.each(this.courses, course => {
        // In support of search, we index nested course data
        course.instructorNames = this.$_.map(course.instructors, 'name')
        course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
        course.isSelectable = !course.hasOptedOut
      })
    },
    methods: {
      mdc(course) {
        return {'border-bottom-zero': course.approvals.length}
      },
      meetings(course) {
        return this.getDisplayMeetings(course)
      },
      tdc(course) {
        return {
          'border-bottom-zero': this.getDisplayMeetings(course).length > 1 || course.approvals.length,
          'pt-3 pb-3': this.$_.size(course.courseCodes) > 1
        }
      }
    }
  }
</script>
