<template>
  <div v-if="!loading" class="pt-3">
    <v-card outlined class="elevation-1 mb-6">
      <v-card-title class="align-start">
        <PageTitle icon="mdi-engine-outline" text="The Engine Room" />
      </v-card-title>
      <v-card-text>
        <div class="mb-3">
          NOTE: You cannot edit a job schedule if the job is either enabled or running.
        </div>
        <v-data-table
          disable-sort
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
                <td class="pb-2 pl-5 pt-2 text-center">
                  <v-btn
                    v-if="!isRunning(job.key)"
                    :id="`run-job-${job.key}`"
                    :aria-label="`Run job ${job.key}`"
                    @click="runJob(job)"
                  >
                    Run <span class="sr-only">job {{ job.name }}</span><v-icon class="pl-2" small>mdi-run-fast</v-icon>
                  </v-btn>
                  <v-progress-circular
                    v-if="isRunning(job.key)"
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
                        :disabled="!job.disabled || isRunning(job.key)"
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
                        Daily at {{ job.schedule.value }} (UTC)
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
      </v-card-text>
    </v-card>
    <JobHistory :job-history="jobHistory" :refreshing="refreshing" />
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
                  :suffix="editJob.schedule.type === 'day_at' ? 'UTC' : ''"
                  :type="editJob.schedule.type === 'day_at' ? 'time' : 'number'"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" text @click="scheduleEditCancel">Close</v-btn>
          <v-btn
            color="blue darken-1"
            :disabled="disableScheduleSave"
            text
            @click="scheduleEditSave"
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
  import PageTitle from '@/components/util/PageTitle'
  import Utils from '@/mixins/Utils'
  import {getJobHistory, getJobSchedule, setJobDisabled, startJob, updateJobSchedule} from '@/api/job'

  export default {
    name: 'Jobs',
    components: {DisableJobToggle, JobHistory, PageTitle},
    mixins: [Context, Utils],
    data: () => ({
      disableScheduleSave: false,
      editJob: undefined,
      editJobDialog: false,
      headers: [
        {},
        {text: 'Name', value: 'name'},
        {text: 'Description', value: 'description'},
        {text: 'Schedule', value: 'schedule'},
        {text: 'Enabled'}
      ],
      jobHistory: undefined,
      jobSchedule: undefined,
      refresher: undefined,
      refreshing: false
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
        this.refresh(true).then(() => {
          this.$ready('The Engine Room')
        })
      })
    },
    destroyed() {
      clearTimeout(this.refresher)
    },
    methods: {
      isRunning(jobKey) {
        return !!this.$_.find(this.jobHistory, h => h.jobKey === jobKey && !h.finishedAt)
      },
      refresh(quietly) {
        this.refreshing = true
        return getJobHistory().then(data => {
          this.jobHistory = data
          this.refreshing = false
          if (!quietly) {
            this.alertScreenReader('Job History refreshed')
          }
          this.scheduleRefresh()
        })
      },
      runJob(job) {
        this.jobHistory.unshift({
          jobKey: job.key,
          failed: false,
          startedAt: this.$moment()
        })
        startJob(job.key).then(() => {})
        const jobName = this.$_.find(this.jobSchedule.jobs, ['key', job.key]).name
        this.snackbarOpen(`${jobName} job started`)
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
        this.refresher = setTimeout(this.refresh, 5000)
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
