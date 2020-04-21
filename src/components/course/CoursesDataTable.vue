<template>
  <div>
    <v-data-table
      id="courses-data-table"
      v-model="undefined"
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
      selectable-key="isSelectable"
      show-select
      :single-select="!onRowsSelected"
      @page-count="pageCurrent = $event"
    >
      <template v-slot:body="{ items }">
        <tbody v-if="items.length">
          <template v-for="course in items">
            <tr :key="course.sectionId">
              <td v-if="onRowsSelected" :class="tdClass(course)" class="text-no-wrap">
                <v-checkbox
                  :id="`checkbox-email-course-${course.sectionId}`"
                  v-model="selectedRows"
                  :disabled="course.hasOptedOut"
                  :value="course"
                ></v-checkbox>
              </td>
              <td :id="`course-name-${course.sectionId}`" :class="tdClass(course)" class="text-no-wrap">
                <router-link
                  v-if="course.room && course.room.capability"
                  :id="`sign-up-${course.sectionId}`"
                  class="subtitle-1"
                  :to="`/approve/${$config.currentTermId}/${course.sectionId}`">
                  {{ course.label }}
                </router-link>
                <span v-if="!course.room || !course.room.capability">{{ course.label }}</span>
              </td>
              <td :id="`section-id-${course.sectionId}`" :class="tdClass(course)" class="text-no-wrap w-10">{{ course.sectionId }}</td>
              <td v-if="includeRoomColumn" :class="tdClass(course)" class="text-no-wrap">
                <router-link
                  v-if="course.room"
                  :id="`course-${course.sectionId}-room-${course.room.id}`"
                  :to="`/room/${course.room.id}`">
                  {{ course.room.location }}
                </router-link>
                <span v-if="!course.room">&mdash;</span>
              </td>
              <td :id="`meeting-days-${course.sectionId}`" :class="tdClass(course)" class="text-no-wrap">{{ course.meetingDays.join(',') }}</td>
              <td :id="`meeting-times-${course.sectionId}`" :class="tdClass(course)" class="text-no-wrap">{{ course.meetingStartTime }} - {{ course.meetingEndTime }}</td>
              <td :id="`course-${course.sectionId}-status`" :class="tdClass(course)" class="w-10">
                <v-tooltip v-if="course.adminApproval" :id="`tooltip-admin-approval-${course.sectionId}`" bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon
                      color="green"
                      class="pa-0"
                      dark
                      v-on="on">
                      mdi-account-check-outline
                    </v-icon>
                  </template>
                  Course Capture Admin {{ course.adminApproval.approvedByUid }}
                  submitted approval on
                  {{ course.adminApproval.createdAt | moment('MMM D, YYYY') }}.
                </v-tooltip>
                {{ course.status || '&mdash;' }}
              </td>
              <td :class="tdClass(course)">
                <div v-for="instructor in course.instructors" :key="instructor.uid" class="mb-1 mt-1 pa-2">
                  <v-tooltip :id="`tooltip-approval-${course.sectionId}-by-${instructor.uid}`" bottom>
                    <template v-slot:activator="{ on }">
                      <v-icon
                        :color="instructor.approval ? 'green' : 'yellow darken-2'"
                        class="pa-0"
                        dark
                        v-on="on">
                        {{ instructor.approval ? 'mdi-check' : 'mdi-alert-circle-outline' }}
                      </v-icon>
                    </template>
                    <div v-if="instructor.approval">
                      Approval submitted on {{ instructor.approval.createdAt | moment('MMM D, YYYY') }}.
                    </div>
                    <div v-if="!instructor.approval">
                      {{ instructor.name }} has not yet approved.
                    </div>
                  </v-tooltip>
                  <router-link :id="`course-${course.sectionId}-instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                    {{ instructor.name }}
                  </router-link> ({{ instructor.uid }})
                </div>
              </td>
              <td :id="`course-${course.sectionId}-publish-types`" :class="tdClass(course)">
                {{ course.publishTypeNames || '&mdash;' }}
              </td>
              <td :class="tdClass(course)">
                <ToggleOptOut :key="course.sectionId" :course="course" :on-toggle="onToggleOptOut" />
              </td>
            </tr>
            <tr v-if="course.approvals.length" :key="`approvals-${course.sectionId}`">
              <td :colspan="headers.length + 1" class="pb-2">
                <div v-if="course.approvals.length" class="pb-3">
                  <div v-for="approval in course.approvals" :key="approval.approvedByUid">
                    "{{ approval.recordingTypeName }}" recording was approved for "{{ approval.publishTypeName }}" by
                    <router-link :id="`instructor-${approval.approvedByUid}-mailto`" :to="`/user/${approval.approvedByUid}`">
                      {{ approval.approvedByUid }}
                    </router-link> ({{ approval.approvedByUid }}) on {{ approval.createdAt | moment('MMM D, YYYY') }}.
                  </div>
                </div>
              </td>
              <td></td>
            </tr>
          </template>
        </tbody>
        <tbody v-if="!items.length">
          <tr>
            <td id="message-when-zero-courses" class="ma-4 text-no-wrap title" :colspan="headers.length">
              {{ messageWhenZeroCourses }}
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
    <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
      <v-pagination
        id="ouija-pagination"
        v-model="pageCurrent"
        :length="pageCount"
        total-visible="10"></v-pagination>
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
        default: true,
        type: Boolean
      },
      messageWhenZeroCourses: {
        required: true,
        type: String
      },
      onRowsSelected: {
        default: undefined,
        type: Function
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
        {text: 'Section', value: 'sectionId'},
        {text: 'Room', value: 'room.location'},
        {text: 'Days', sortable: false},
        {text: 'Time', sortable: false},
        {text: 'Status', value: 'status'},
        {text: 'Instructor(s)', value: 'instructorNames'},
        {text: 'Publish', value: 'publishTypeNames'},
        {text: 'Opt out', value: 'hasOptedOut', sortable: false}
      ],
      pageCount: undefined,
      pageCurrent: 1,
      selectedRows: [],
      selectedFilter: 'Not Invited'
    }),
    watch: {
      selectedRows(rows) {
        if (this.onRowsSelected) {
          this.onRowsSelected(rows)
        }
      }
    },
    mounted() {
      this.headers = this.includeRoomColumn ? this.headers : this.$_.filter(this.headers, h => h.text !== 'Room')
      if (!this.onRowsSelected) {
        this.hideSelectCoursesColumn()
      }
      this.$_.each(this.courses, course => {
        // In support of search, we index nested course data
        course.instructorNames = this.$_.map(course.instructors, 'name')
        course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
        course.isSelectable = !course.hasOptedOut
      })
    },
    methods: {
      hideSelectCoursesColumn() {
        const hideColumn = () => {
          let el = document.getElementById('courses-data-table')
          el = el && el.querySelector('table tr th')
          if (el) {
            el.style.display = 'none'
          }
          return !!el
        }
        if (!hideColumn()) {
          this.onNextTick(hideColumn)
        }
      },
      tdClass(course) {
        return course.approvals.length ? 'border-bottom-zero text-no-wrap' : 'text-no-wrap'
      }
    }
  }
</script>
