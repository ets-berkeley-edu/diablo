<template>
  <div v-if="!loading">
    <div class="pb-8">
      <v-card outlined class="elevation-1">
        <v-card-title class="align-start">
          <div class="pt-2">
            <h1><v-icon class="pb-3" large>mdi-wrench-outline</v-icon> Jobs</h1>
          </div>
          <v-spacer></v-spacer>
          <v-dialog v-model="jobScheduleDialog">
            <template v-slot:activator="{ on }">
              <v-btn color="accent" dark v-on="on">
                Job Schedule
              </v-btn>
            </template>
            <v-card>
              <v-card-title class="headline grey lighten-2" primary-title>
                Job Schedule
              </v-card-title>
              <v-card-text>
                <div class="body-2 ma-3">
                  <div>
                    <span class="font-weight-bold">Auto-start:</span> {{ jobSchedule.autoStart }}
                  </div>
                  <div>
                    <span class="font-weight-bold">Seconds between jobs check:</span> {{ jobSchedule.secondsBetweenJobsCheck }}
                  </div>
                </div>
                <v-simple-table>
                  <template v-slot:default>
                    <thead>
                      <tr>
                        <th>Job Name</th>
                        <th>Description</th>
                        <th>Schedule</th>
                      </tr>
                    </thead>
                    <tbody v-if="jobSchedule.jobs.length">
                      <template v-for="(job, index) in jobSchedule.jobs">
                        <tr :key="job.name">
                          <td :id="`job-name-${index}`" class="text-no-wrap">
                            {{ job.name }}
                          </td>
                          <td :id="`job-description-${index}`">
                            {{ job.description }}
                          </td>
                          <td :id="`job-schedule-${index}`" class="text-no-wrap">
                            {{ job.schedule.type }}: {{ job.schedule.value }}
                          </td>
                        </tr>
                      </template>
                    </tbody>
                    <tbody v-if="!jobSchedule.jobs.length">
                      <tr>
                        <td>
                          No scheduled jobs
                        </td>
                      </tr>
                    </tbody>
                  </template>
                </v-simple-table>
              </v-card-text>
              <v-divider></v-divider>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  color="primary"
                  text
                  @click="jobScheduleDialog = false"
                >
                  Close
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-card-title>
        <v-data-table
          :headers="headers"
          hide-default-footer
          :items="jobs"
          dense
        >
          <template v-slot:body="{ items }">
            <tbody>
              <tr v-if="!items.length">
                <td id="message-when-zero-jobs" class="pa-4 text-no-wrap title" :colspan="headers.length">
                  No jobs
                </td>
              </tr>
              <tr v-for="job in items" :key="job.key">
                <td class="w-auto">
                  <v-btn
                    :id="`run-job-${job.key}`"
                    :aria-label="`Run job ${job.key}`"
                    fab
                    small
                    @click="start(job.key)"
                  >
                    <v-icon>mdi-run-fast</v-icon>
                  </v-btn>
                </td>
                <td class="pr-4 text-no-wrap">
                  {{ job.key }}
                </td>
                <td>
                  {{ job.description }}
                </td>
              </tr>
            </tbody>
          </template>
        </v-data-table>
      </v-card>
    </div>
    <v-card outlined class="elevation-1">
      <v-card-title class="align-start">
        <div class="pt-2">
          <h2><v-icon class="pb-1" large>mdi-history</v-icon> Job History</h2>
        </div>
        <v-spacer></v-spacer>
        <v-text-field
          v-if="jobHistory.length"
          v-model="search"
          append-icon="search"
          label="Search History"
          single-line
          hide-details
        ></v-text-field>
      </v-card-title>
      <v-data-table
        :headers="jobHistoryHeaders"
        hide-default-footer
        :items="jobHistory"
        :loading="refreshing"
        no-results-text="No matching jobs"
        :options="options"
        :page.sync="options.page"
        :search="search"
        @page-count="pageCount = $event"
      >
        <template v-slot:item.failed="{ item }">
          <v-icon v-if="item.finishedAt" :color="item.failed ? 'red' : 'light-green'">
            {{ item.failed ? 'mdi-exclamation-thick' : 'mdi-check-bold' }}
          </v-icon>
          <v-progress-circular
            v-if="!item.finishedAt"
            :indeterminate="true"
            rotate="5"
            size="24"
            width="4"
            color="orange"
          ></v-progress-circular>
        </template>
        <template v-slot:item.startedAt="{ item }">
          {{ item.startedAt | moment(dateFormat) }}
        </template>
        <template v-slot:item.finishedAt="{ item }">
          <span v-if="item.finishedAt">{{ item.finishedAt | moment(dateFormat) }}</span>
        </template>
      </v-data-table>
      <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
        <v-pagination
          id="rooms-pagination"
          v-model="options.page"
          :length="pageCount"
          total-visible="10"
        ></v-pagination>
      </div>
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getAvailableJobs, getJobHistory, getJobSchedule, startJob} from '@/api/job'

  export default {
    name: 'Attic',
    mixins: [Context, Utils],
    data: () => ({
      dateFormat: 'dddd, MMMM Do, h:mm:ss a',
      daysCount: 3,
      headers: [
        {text: 'Job', class: 'w-10', sortable: false},
        {text: 'Key', value: 'key', sortable: false},
        {text: 'Description', value: 'description'}
      ],
      jobHistoryHeaders: [
        {text: 'Key', value: 'jobKey'},
        {text: 'Status', value: 'failed'},
        {text: 'Started', value: 'startedAt'},
        {text: 'Finished', value: 'finishedAt'}
      ],
      jobHistory: undefined,
      jobs: undefined,
      jobSchedule: undefined,
      jobScheduleDialog: false,
      options: {
        page: 1,
        itemsPerPage: 50
      },
      pageCount: undefined,
      refresher: undefined,
      refreshing: false,
      search: undefined
    }),
    created() {
      this.$loading()
      getAvailableJobs().then(data => {
        this.jobs = data
        getJobHistory(this.daysCount).then(data => {
          this.jobHistory = data
          this.scheduleRefresh()
          getJobSchedule().then(data => {
            this.jobSchedule = data
            this.$ready()
          })
        }).catch(this.$ready)
      }).catch(this.$ready)
    },
    destroyed() {
      clearTimeout(this.refresher)
    },
    methods: {
      refresh() {
        this.refreshing = true
        getJobHistory(this.daysCount).then(data => {
          this.jobHistory = data
          this.refreshing = false
          this.scheduleRefresh()
        })
      },
      scheduleRefresh() {
        // Clear previous job, if pending
        clearTimeout(this.refresher)
        this.refresher = setTimeout(this.refresh, 5000)
      },
      start(jobKey) {
        startJob(jobKey).then(() => {
          this.refresh()
        })
      }
    }
  }
</script>
