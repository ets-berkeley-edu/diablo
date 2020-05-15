<template>
  <div v-if="!loading" class="pt-3">
    <h1 class="sr-only">Jobs</h1>
    <v-card outlined class="elevation-1 mb-6">
      <v-card-title class="align-start">
        <div class="pt-2">
          <h2><v-icon class="pb-1" large>mdi-timer-sand</v-icon> Job Schedule</h2>
        </div>
      </v-card-title>
      <v-data-table
        :headers="headers"
        hide-default-footer
        :items="jobSchedule.jobs"
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
              <td class="pa-2 w-auto">
                <v-btn
                  :id="`run-job-${job.key}`"
                  :aria-label="`Run job ${job.key}`"
                  fab
                  x-small
                  @click="start(job.key)"
                >
                  <v-icon small>mdi-run-fast</v-icon>
                </v-btn>
              </td>
              <td class="pr-4 text-no-wrap">
                {{ $_.replace(job.name, 'Job', '') }}
              </td>
              <td>
                {{ job.description }}
              </td>
              <td :id="`job-schedule-${job.key}`" class="text-no-wrap">
                <span v-if="job.schedule.type === 'day_at'">Daily at {{ job.schedule.value }}</span>
                <span v-if="job.schedule.type !== 'day_at'">Every {{ job.schedule.value }} {{ job.schedule.type }}</span>
              </td>
              <td>
                <v-switch
                  :id="`job-${job.key}-disabled`"
                  v-model="job.disabled"
                  :color="job.disabled ? 'red': 'green'"
                  :aria-label="`Job ${job.name} is ${job.disabled ? 'disabled' : 'enabled'}`"
                  @change="toggleDisabled(job)"
                >
                </v-switch>
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
    </v-card>
    <v-card outlined class="elevation-1">
      <v-card-title class="align-start">
        <div class="pt-2">
          <h2><v-icon class="pb-1" large>mdi-history</v-icon> History</h2>
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
    <v-bottom-sheet v-model="richardPryor">
      <v-sheet class="text-center" dark height="800px">
        <v-btn
          id="get-the-damn-bed-off-my-foot"
          class="mt-6"
          color="primary"
          @click="richardPryor = !richardPryor"
        >
          Close
        </v-btn>
        <div class="py-3">
          <img alt="The bed is on my foot!" src="@/assets/the-bed-is-on-my-foot.jpg">
        </div>
      </v-sheet>
    </v-bottom-sheet>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getJobHistory, getJobSchedule, setJobDisabled, startJob, updateJobSchedule} from '@/api/job'

  export default {
    name: 'Attic',
    mixins: [Context, Utils],
    data: () => ({
      dateFormat: 'dddd, MMMM Do, h:mm:ss a',
      daysCount: 3,
      headers: [
        {sortable: false},
        {text: 'Name', value: 'name', sortable: false},
        {text: 'Description', value: 'description', sortable: false},
        {text: 'Schedule', value: 'schedule', sortable: false},
        {text: 'Disable', value: 'disabled'}
      ],
      jobHistoryHeaders: [
        {text: 'Key', value: 'jobKey'},
        {text: 'Status', value: 'failed'},
        {text: 'Started', value: 'startedAt'},
        {text: 'Finished', value: 'finishedAt'}
      ],
      jobHistory: undefined,
      jobSchedule: undefined,
      options: {
        page: 1,
        itemsPerPage: 50
      },
      pageCount: undefined,
      refresher: undefined,
      refreshing: false,
      richardPryor: false,
      search: undefined
    }),
    watch: {
      search(value) {
        this.richardPryor = value && value.toLowerCase() === 'the bed is on my foot'
      }
    },
    created() {
      this.$loading()
      getJobHistory(this.daysCount).then(data => {
        this.jobHistory = data
        this.scheduleRefresh()
        getJobSchedule().then(data => {
          this.jobSchedule = data
          this.$ready()
        })
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
      },
      toggleDisabled(job) {
        setJobDisabled(job.id, job.disabled).then(data => job.disabled = data.disabled)
      },
      updateSchedule(job) {
        updateJobSchedule(job.id, job.schedule.type, job.schedule.value).then(data => job.schedule = data.schedule)
      }
    }
  }
</script>
