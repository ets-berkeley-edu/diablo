<template>
  <div v-if="!loading">
    <div class="pb-8">
      <v-card outlined class="elevation-1">
        <v-card-title class="align-start">
          <div class="pt-2">
            <h1><v-icon class="pb-3" large>mdi-wrench-outline</v-icon> Jobs</h1>
          </div>
          <v-spacer></v-spacer>
        </v-card-title>
        <v-data-table
          :headers="headers"
          hide-default-footer
          :items="jobs"
          dense
          no-results-text="No jobs?!"
        >
          <template v-slot:body="{ items }">
            <tbody>
              <tr v-if="!items.length" id="no-jobs">
                <td>
                  No jobs found.
                </td>
              </tr>
              <tr v-for="job in items" :key="job.key">
                <td class="w-auto">
                  <v-btn
                    :id="`run-job-${job.key}`"
                    :aria-label="`Run job ${job.key}`"
                    fab
                    small
                    @click="start(job.key)">
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
          total-visible="10"></v-pagination>
      </div>
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getAvailableJobs, getJobHistory, startJob} from '@/api/job'

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
      options: {
        page: 1,
        itemsPerPage: 50
      },
      pageCount: undefined,
      refresher: undefined,
      refreshing: false,
      search: undefined
    }),
    mounted() {
      this.$loading()
      getAvailableJobs().then(data => {
        this.jobs = data
        getJobHistory(this.daysCount).then(data => {
          this.jobHistory = data
          this.scheduleRefresh()
          this.$ready()
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
