<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <h2><v-icon class="pb-3" large>mdi-auto-fix</v-icon> The Ouija Board</h2>
        <div class="pt-4">
          <v-btn id="btn-send-email" :disabled="!selectedRows.length" @click="sendEmail()">Send Email</v-btn>
        </div>
      </div>
      <v-spacer></v-spacer>
      <div class="float-right w-50">
        <v-text-field
          id="input-search"
          v-model="search"
          append-icon="mdi-magnify"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
        <v-select
          id="ouija-filter-options"
          v-model="selectedFilter"
          color="secondary"
          :items="$config.searchFilterOptions"
          @change="refresh"
        ></v-select>
      </div>
    </v-card-title>
    <v-data-table
      v-model="selectedRows"
      :headers="headers"
      hide-default-footer
      item-key="sectionId"
      :items="courses"
      :loading="refreshing"
      :options="options"
      :page.sync="options.page"
      :search="search"
      selectable-key="isSelectable"
      show-select
      :single-select="false"
      @page-count="pageCount = $event"
    >
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-if="!items.length && !refreshing">
            <td colspan="10">
              <div class="ma-4 text-no-wrap title">
                <span v-if="search" id="no-results-for-search">No results for '{{ search }}'</span>
                <span v-if="!search" id="no-results-in-filter">No '{{ selectedFilter }}' courses</span>
              </div>
            </td>
          </tr>
          <tr v-for="item in items" :key="item.name">
            <td class="text-no-wrap">
              <v-checkbox
                :id="`checkbox-email-course-${item.sectionId}`"
                v-model="selectedRows"
                :disabled="item.hasOptedOut"
                :value="item"
              ></v-checkbox>
            </td>
            <td :id="`course-name-${item.sectionId}`" class="text-no-wrap">
              <router-link
                v-if="item.room.capability"
                :id="`sign-up-${item.sectionId}`"
                class="subtitle-1"
                :to="`/approve/${$config.currentTermId}/${item.sectionId}`">
                {{ item.label }}
              </router-link>
              <span v-if="!item.room.capability">{{ item.label }}</span>
            </td>
            <td :id="`section-id-${item.sectionId}`" class="text-no-wrap w-10">{{ item.sectionId }}</td>
            <td class="text-no-wrap">
              <router-link
                v-if="item.room"
                :id="`course-${item.sectionId}-room-${item.room.id}`"
                :to="`/room/${item.room.id}`">
                {{ item.room.location }}
              </router-link>
              <span v-if="!item.room">&nbsp;</span>
            </td>
            <td :id="`meeting-days-${item.sectionId}`" class="text-no-wrap">{{ item.meetingDays.join(',') }}</td>
            <td :id="`meeting-times-${item.sectionId}`" class="text-no-wrap">{{ item.meetingStartTime }} - {{ item.meetingEndTime }}</td>
            <td :id="`course-${item.sectionId}-status`" class="w-10">
              <v-tooltip v-if="item.adminApproval" :id="`tooltip-admin-approval-${item.sectionId}`" bottom>
                <template v-slot:activator="{ on }">
                  <v-icon
                    color="green"
                    class="pa-0"
                    dark
                    v-on="on">
                    mdi-account-check-outline
                  </v-icon>
                </template>
                Course Capture Admin {{ item.adminApproval.approvedByUid }}
                submitted approval on
                {{ item.adminApproval.createdAt | moment('MMM D, YYYY') }}.
              </v-tooltip>
              {{ item.status || '&mdash;' }}
            </td>
            <td>
              <div v-for="instructor in item.instructors" :key="instructor.uid" class="mb-1 mt-1 pa-2">
                <v-tooltip :id="`tooltip-approval-${item.sectionId}-by-${instructor.uid}`" bottom>
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
                <router-link :id="`course-${item.sectionId}-instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                  {{ instructor.name }}
                </router-link> ({{ instructor.uid }})
              </div>
            </td>
            <td :id="`course-${item.sectionId}-publish-types`">
              {{ item.publishTypeNames || '&mdash;' }}
            </td>
            <td>
              <ToggleOptOut :key="item.sectionId" :course="item" :on-toggle="onToggleOptOut" />
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
    <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
      <v-pagination
        id="ouija-pagination"
        v-model="options.page"
        :length="pageCount"
        total-visible="10"></v-pagination>
    </div>
  </v-card>
</template>

<script>
  import Context from '@/mixins/Context'
  import ToggleOptOut from '@/components/course/ToggleOptOut'
  import Utils from '@/mixins/Utils'
  import {queueEmails} from '@/api/email'
  import {getCourses} from '@/api/course'

  export default {
    name: 'Ouija',
    components: {ToggleOptOut},
    mixins: [Context, Utils],
    data: () => ({
      courses: undefined,
      headers: [
        {text: 'Course', value: 'label'},
        {text: 'Section', value: 'sectionId'},
        {text: 'Room', value: 'meetingLocation'},
        {text: 'Days', sortable: false},
        {text: 'Time', sortable: false},
        {text: 'Status', value: 'status'},
        {text: 'Instructor(s)', value: 'instructorNames'},
        {text: 'Publish', value: 'publishTypeNames'},
        {text: 'Opt out', value: 'hasOptedOut', sortable: false}
      ],
      options: {
        page: 1,
        itemsPerPage: 50
      },
      pageCount: undefined,
      refreshing: undefined,
      search: '',
      selectedFilter: 'Not Invited',
      selectedRows: []
    }),
    watch: {
      selectedRows(rows) {
        const newCount = this.$_.size(this.$_.filter(rows, ['hasOptedOut', false]))
        if (newCount >= this.options.itemsPerPage) {
          this.snackbarOpen(`${newCount} courses selected`)
        }
      }
    },
    created() {
      this.$loading()
      this.refresh()
    },
    methods: {
      omitCourse(course) {
        let indexOf = this.courses.findIndex(c => c.sectionId === course.sectionId)
        if (indexOf >= 0) {
          this.courses.splice(indexOf, 1)
        }
      },
      onToggleOptOut(course) {
        const omitCourse = course.hasOptedOut ? this.$_.includes(['Invited', 'Not Invited'], this.selectedFilter) : this.selectedFilter === 'Do Not Email'
        if (omitCourse) {
          this.omitCourse(course)
          this.snackbarOpen(`${course.label} removed from list. It ${course.hasOptedOut ? 'will not' : 'will'} receive email.`)
        }
      },
      refresh() {
        const done = () => {
          this.selectedRows = []
          this.refreshing = false
          this.$ready()
        }
        this.refreshing = true
        getCourses(this.selectedFilter, this.$config.currentTermId).then(data => {
          this.courses = data
          this.$_.each(this.courses, course => {
            // In support of search, we index nested course data
            course.instructorNames = this.$_.map(course.instructors, 'name')
            course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
            course.isSelectable = !course.hasOptedOut
          })
          done()
        }).catch(done)
      },
      sendEmail() {
        if (this.selectedRows.length) {
          const sectionIds = this.$_.map(this.selectedRows, 'sectionId')
          queueEmails('invitation', sectionIds, this.$config.currentTermId).then(data => {
            this.snackbarOpen(data.message)
          })
        }
      }
    }
  }
</script>
