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
      >
        <template v-slot:body="{ items }">
          <tbody>
            <tr v-if="!items.length">
              <td id="message-when-zero-jobs" class="pa-4 text-no-wrap title" :colspan="headers.length">
                No jobs
              </td>
            </tr>
            <tr v-for="job in items" :key="job.key">
              <td class="pb-2 pl-5 pt-2">
                <v-btn
                  v-if="!$_.includes(runningJobs, job.key)"
                  :id="`run-job-${job.key}`"
                  :aria-label="`Run job ${job.key}`"
                  fab
                  x-small
                  @click="start(job.key)"
                >
                  <v-icon small>mdi-run-fast</v-icon>
                </v-btn>
                <v-progress-circular
                  v-if="$_.includes(runningJobs, job.key)"
                  class="ml-1"
                  indeterminate
                  size="24"
                  width="4"
                ></v-progress-circular>
              </td>
              <td class="pr-4 text-no-wrap">
                {{ job.name }}
              </td>
              <td class="pb-2 pt-2">
                <span v-html="job.description"></span>
              </td>
              <td :id="`job-schedule-${job.key}`" class="text-no-wrap">
                <div class="d-flex align-center">
                  <div>
                    <v-btn
                      :id="`edit-job-schedule-${job.key}`"
                      :aria-label="`Edit job schedule ${job.key}`"
                      class="pr-2"
                      small
                      text
                      @click.stop="scheduleEditOpen(job)"
                    >
                      <v-icon>mdi-playlist-edit</v-icon>
                    </v-btn>
                  </div>
                  <div>
                    <span v-if="job.schedule.type === 'day_at'" :for="`edit-job-schedule-${job.key}`">
                      Daily at {{ job.schedule.value }}
                    </span>
                    <span v-if="job.schedule.type !== 'day_at'" :for="`edit-job-schedule-${job.key}`">
                      Every {{ job.schedule.value }} {{ job.schedule.type }}
                    </span>
                  </div>
                </div>
              </td>
              <td>
                <DisableJobToggle :key="job.disabled" :job="job" :on-change="toggleDisabled" />
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
    </v-card>
    <JobHistory :ping="pingJobHistory" />
    <v-dialog v-model="editJobDialog" max-width="400px" persistent>
      <v-card>
        <v-card-title>
          <span class="headline">{{ $_.get(editJob, 'name') }} Schedule</span>
        </v-card-title>
        <v-card-text>
          <v-container v-if="editJob">
            <v-row>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editJob.schedule.type"
                  :items="['day_at', 'minutes', 'seconds']"
                  label="Type"
                  required
                  @change="editJob.schedule.value = ''"
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="editJob.schedule.value"
                  required
                  :suffix="editJob.schedule.type === 'day_at' ? 'PST': ''"
                  :type="editJob.schedule.type === 'day_at' ? 'time': 'number'"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" text @click="scheduleEditCancel()">Close</v-btn>
          <v-btn
            color="blue darken-1"
            :disabled="disableScheduleSave"
            text
            @click="scheduleEditSave()"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import DisableJobToggle from '@/components/job/DisableJobToggle'
  import JobHistory from '@/components/job/JobHistory'
  import Utils from '@/mixins/Utils'
  import {getJobSchedule, getRunningJobs, setJobDisabled, startJob, updateJobSchedule} from '@/api/job'

  export default {
    name: 'Jobs',
    components: {DisableJobToggle, JobHistory},
    mixins: [Context, Utils],
    data: () => ({
      disableScheduleSave: false,
      editJob: undefined,
      editJobDialog: false,
      headers: [
        {sortable: false},
        {text: 'Name', value: 'name', sortable: false},
        {text: 'Description', value: 'description', sortable: false},
        {text: 'Schedule', value: 'schedule', sortable: false},
        {text: 'Enabled', sortable: false}
      ],
      jobSchedule: undefined,
      pingJobHistory: undefined,
      refresher: undefined,
      runningJobs: undefined
    }),
    watch: {
      editJob: {
        deep: true,
        handler(job) {
          this.disableScheduleSave = !this.$_.get(job, 'schedule.value') || parseInt(job.schedule.value) < 0
        }
      }
    },
    created() {
      this.$loading()
      getJobSchedule().then(data => {
        this.jobSchedule = data
        this.$ready('Jobs')
        this.refresh()
      })
    },
    destroyed() {
      clearTimeout(this.refresher)
    },
    methods: {
      refresh() {
        getRunningJobs().then(data => {
          this.runningJobs = this.$_.map(data, 'jobKey')
          this.scheduleRefresh()
        })
      },
      scheduleEditCancel() {
        this.editJob = undefined
        this.editJobDialog = false
        this.alertScreenReader('Cancelled')
      },
      scheduleEditOpen(job) {
        this.editJob = this.$_.cloneDeep(job)
        this.editJobDialog = true
        this.alertScreenReader(`Opened dialog to edit job ${job.name}`)
      },
      scheduleEditSave() {
        updateJobSchedule(
          this.editJob.id,
          this.editJob.schedule.type,
          this.editJob.schedule.value
        ).then(() => {
          const match = this.$_.find(this.jobSchedule.jobs, ['id', this.editJob.id])
          match.schedule = this.editJob.schedule
          this.editJob = undefined
          this.editJobDialog = false
          this.alertScreenReader(`Job '${match.name}' was updated.`)
        })
      },
      scheduleRefresh() {
        clearTimeout(this.refresher)
        this.refresher = setTimeout(this.refresh, 3000)
      },
      start(jobKey) {
        this.runningJobs.push(jobKey)
        setTimeout(() => this.pingJobHistory = this.$moment().valueOf(), 1000)
        startJob(jobKey).then(() => {
          this.pingJobHistory = this.$moment().valueOf()
          this.refresh()
          this.alertScreenReader(`Job ${jobKey} started`)
        })
      },
      toggleDisabled(job, isDisabled) {
        setJobDisabled(job.id, isDisabled).then(data => {
          job.disabled = data.disabled
          this.alertScreenReader(`Job '${job.name}' ${job.disabled ? 'disabled' : 'enabled'}`)
        })
      }
    }
  }
</script>
