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
          v-model="search"
          append-icon="mdi-magnify"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
        <v-select
          id="select-filter"
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
      show-select
      :single-select="false"
      @page-count="pageCount = $event"
    >
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-if="!items.length && !refreshing">
            <td>
              <div v-if="search">
                No matching items
              </div>
              <div v-if="!search" class="ma-4 text-no-wrap title">
                No '{{ selectedFilter }}' courses
              </div>
            </td>
          </tr>
          <tr v-for="item in items" :key="item.name">
            <td class="text-no-wrap">
              <v-checkbox :id="`checkbox-email-course-${item.sectionId}`" v-model="selectedRows" :value="item"></v-checkbox>
            </td>
            <td class="text-no-wrap">{{ item.courseName }}</td>
            <td class="text-no-wrap">{{ item.sectionId }}</td>
            <td class="text-no-wrap">
              <router-link
                v-if="item.room"
                :id="`course-${item.sectionId}-room-${item.room.id}`"
                :to="`/room/${item.room.id}`">
                {{ item.room.location }}
              </router-link>
              <span v-if="!item.room">&nbsp;</span>
            </td>
            <td class="text-no-wrap">{{ item.meetingDays.join(',') }}</td>
            <td class="text-no-wrap">{{ item.meetingStartTime }} - {{ item.meetingEndTime }}</td>
            <td class="text-no-wrap">TODO: {{ item.status }}</td>
            <td>
              <div v-for="instructor in item.instructors" :key="instructor.uid">
                <router-link :id="`instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                  {{ instructor.name }}
                </router-link> ({{ instructor.uid }})
              </div>
            </td>
            <td>
              <span v-if="item.approvals.length">
                {{ $_.last(item.approvals).publishTypeName }}
              </span>
            </td>
            <td>
              <ToggleOptOut :course="item" :on-toggle="refresh" />
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
      confirmation: undefined,
      courses: undefined,
      headers: [
        {text: 'Course', value: 'courseName'},
        {text: 'Section', value: 'sectionId'},
        {text: 'Room', value: 'room.location'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false},
        {text: 'Status', value: 'status'},
        {text: 'Instructor(s)', value: 'instructorNames'},
        {text: 'Recording', value: 'recording', sortable: false},
        {text: 'Opt out', value: 'hasOptedOut'}
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
    created() {
      this.$loading()
      this.refresh()
    },
    methods: {
      refresh() {
        const done = () => {
          this.selectedRows = []
          this.refreshing = false
          this.$ready()
        }
        this.refreshing = true
        getCourses(this.selectedFilter, this.$config.currentTermId).then(data => {
          this.courses = data
          done()
        }).catch(done)
      },
      sendEmail() {
        if (this.selectedRows.length) {
          const emailTemplateType = undefined
          const sectionIds = undefined
          queueEmails(emailTemplateType, sectionIds, this.$config.currentTermId).then(data => {
            this.confirmation = data.message
          })
        }
      }
    }
  }
</script>
