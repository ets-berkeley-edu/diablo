<template>
  <div v-if="!contextStore.loading" class="pt-2">
    <v-card class="border-sm mb-4">
      <v-card-title>
        <PageTitle
          :icon="mdiHandsPray"
          sub-title="A sacred place for Admin users."
          text="The Chancel"
        />
      </v-card-title>
      <v-card-text>
        <v-data-table
          id="job-schedule-table"
          disable-sort
          :headers="headers"
          hide-default-footer
          :items="jobSchedule.jobs"
          :items-per-page="-1"
          no-data-text="No jobs"
        >
          <template #headers="{columns}">
            <tr>
              <th
                v-for="(column, colIndex) in columns"
                :id="`job-schedule-${column.value}-th`"
                :key="colIndex"
                class="font-size-12 font-weight-bold text-medium-emphasis text-no-wrap"
                scope="col"
              >
                <span :class="`${column.class} ${column.value === 'schedule' ? 'pl-2' : ''}`">{{ column.title }}</span>
              </th>
            </tr>
          </template>
          <template #body="{items}">
            <tr v-for="job in items" :key="job.key">
              <td
                :id="`job-schedule-${job.key}-status`"
                class="text-center"
                columnheader="job-schedule-status-th"
              >
                <div class="d-flex align-center">
                  <v-btn
                    :id="`run-job-${job.key}`"
                    :aria-label="`Run job ${job.name}`"
                    bg-color="transparent"
                    :disabled="isRunning(job.key)"
                    icon
                    size="large"
                    @click="runJob(job)"
                  >
                    <v-icon
                      v-if="!isRunning(job.key)"
                      color="light-green"
                      :icon="mdiPlay"
                      size="36"
                    />
                    <v-progress-circular
                      v-if="isRunning(job.key)"
                      :aria-label="`${job.name} job is running`"
                      color="light-green"
                      indeterminate
                      size="56"
                      width="8"
                    />
                  </v-btn>
                </div>
              </td>
              <td
                :id="`job-schedule-${job.key}-name`"
                class="job-name text-no-wrap"
                columnheader="job-schedule-name-th"
              >
                <span class="font-weight-bold font-size-16">{{ job.name }}</span>
              </td>
              <td
                :id="`job-schedule-${job.key}-description`"
                class="pb-2 pt-2"
                columnheader="job-schedule-description-th"
              >
                <span v-html="job.description"></span>
              </td>
              <td
                :id="`job-schedule-${job.key}-schedule`"
                class="text-no-wrap pl-0"
                columnheader="job-schedule-schedule-th"
              >
                <div v-if="job.isSchedulable" class="d-flex align-center">
                  <v-btn
                    :id="`edit-job-schedule-${job.key}`"
                    :aria-label="`Edit job schedule ${job.key}`"
                    :disabled="!job.disabled || isRunning(job.key)"
                    class="mr-2"
                    :icon="mdiPlaylistEdit"
                    variant="text"
                    @click.stop="scheduleEditOpen(job)"
                  >
                  </v-btn>
                  <div>
                    <span v-if="job.schedule.type === 'day_at'" :for="`edit-job-schedule-${job.key}`">
                      Daily at {{ job.schedule.value }} (UTC)
                    </span>
                    <span v-if="job.schedule.type !== 'day_at'" :for="`edit-job-schedule-${job.key}`">
                      Every {{ job.schedule.value }} {{ job.schedule.type }}
                    </span>
                  </div>
                </div>
                <div v-if="!job.isSchedulable" class="d-flex justify-start">
                  <v-icon class="mx-4" color="red" :icon="mdiAlert" />
                  This job is not schedulable.
                </div>
              </td>
              <td :id="`job-schedule-${job.key}-disable`" columnheader="job-schedule-disable-th">
                <div class="d-flex align-center">
                  <DisableJobToggle
                    :key="job.disabled"
                    :disabled="!job.isSchedulable"
                    :job="job"
                    :on-change="toggleJobDisabled"
                  />
                </div>
              </td>
            </tr>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
    <JobHistory :job-history="jobHistory" :refreshing="refreshing" />
    <v-dialog
      v-model="editJobDialog"
      aria-labelledby="job-schedule-modal-header"
      max-width="600"
      min-width="400"
      persistent
      width="50%"
    >
      <v-card class="modal-content">
        <v-card-title>
          <h2 id="job-schedule-modal-header"><span class="sr-only">Edit </span>{{ get(editJob, 'name') }} Schedule</h2>
        </v-card-title>
        <v-card-text>
          <v-container v-if="editJob">
            <v-row>
              <v-col cols="12" sm="6">
                <v-select
                  id="schedule-type-select"
                  v-model="editJob.schedule.type"
                  :items="['day_at', 'minutes', 'seconds']"
                  label="Type"
                  :menu-props="{eager: true, id: 'schedule-type-select-menu'}"
                  required
                  @update:model-value="editJob.schedule.value = ''"
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  id="schedule-value-input"
                  v-model="editJob.schedule.value"
                  :label="editJob.schedule.type === 'day_at' ? 'Time' : 'Duration'"
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
          <ProgressButton
            id="edit-schedule-save-btn"
            :action="scheduleEditSave"
            :disabled="disableScheduleSave"
            :in-progress="isSavingJob"
            :text="isSavingJob ? 'Saving' : 'Save'"
          />
          <v-btn
            id="edit-schedule-cancel-btn"
            variant="text"
            @click="scheduleEditCancel(editJob)"
          >
            Cancel
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import {cloneDeep, find, get} from 'lodash'
import {mdiAlert, mdiHandsPray, mdiPlay, mdiPlaylistEdit} from '@mdi/js'
import {onBeforeMount, onMounted, ref, watch} from 'vue'
import DisableJobToggle from '@/components/job/DisableJobToggle'
import JobHistory from '@/components/job/JobHistory'
import PageTitle from '@/components/util/PageTitle'
import ProgressButton from '@/components/util/ProgressButton'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {getJobHistory, getJobSchedule, setJobDisabled, startJob, updateJobSchedule} from '@/api/job'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const disableScheduleSave = ref(false)
const editJob = ref()
const editJobDialog = ref(false)
const headers = [
  {title: 'Job Status', class: 'sr-only', value: 'status'},
  {title: 'Name', class: 'sr-only', value: 'name'},
  {title: 'Description', value: 'description'},
  {title: 'Schedule', value: 'schedule'},
  {title: 'Enabled', value: 'enabled'}
]
const isSavingJob = ref(false)
const jobHistory = ref([])
const jobSchedule = ref({
  jobs: []
})
const refresher = ref()
const refreshing = ref(false)

watch(editJob, job => {
  // deep: true,
  disableScheduleSave.value = !get(job, 'schedule.value') || parseInt(job.schedule.value) < 0
})
onMounted(() => {
  contextStore.loadingStart()
  getJobSchedule().then(data => {
    jobSchedule.value = data
    refresh().then(() => {
      contextStore.loadingComplete()
    })
  })
})
onBeforeMount(() => {
  clearTimeout(refresher.value)
})

const isRunning = (jobKey) => {
  return !!find(jobHistory.value, h => h.jobKey === jobKey && !h.finishedAt)
}

const refresh = () => {
  refreshing.value = true
  return getJobHistory().then(data => {
    jobHistory.value = data
    refreshing.value = false
    scheduleRefresh()
  })
}

const runJob = (job) => {
  jobHistory.value.unshift({
    jobKey: job.key,
    failed: false,
    startedAt: new Date()
  })
  startJob(job.key).then(() => {})
  const jobName = find(jobSchedule.value.jobs, ['key', job.key]).name
  contextStore.snackbarOpen(`${jobName} job started`)
  putFocusNextTick('btn-close-alert')
}

const scheduleEditCancel = (job) => {
  editJob.value = undefined
  editJobDialog.value = false
  alertScreenReader('Cancelled')
  putFocusNextTick(`edit-job-schedule-${job.key}`)
}

const scheduleEditOpen = (job) => {
  editJob.value = cloneDeep(job)
  editJobDialog.value = true
  putFocusNextTick('schedule-type-select')
}

const scheduleEditSave = () => {
  isSavingJob.value = true
  updateJobSchedule(
    editJob.value.id,
    editJob.value.schedule.type,
    editJob.value.schedule.value
  ).then(() => {
    const match = find(jobSchedule.value.jobs, ['id', editJob.value.id])
    match.schedule = editJob.value.schedule
    editJob.value = undefined
    editJobDialog.value = false
    isSavingJob.value = false
    alertScreenReader(`Job '${match.name}' was updated.`)
    putFocusNextTick(`edit-job-schedule-${match.key}`)
  })
}

const scheduleRefresh = () => {
  clearTimeout(refresher.value)
  refresher.value = setTimeout(refresh, 5000)
}

const toggleJobDisabled = (job, isDisabled) => {
  setJobDisabled(job.id, isDisabled).then(data => {
    job.disabled = data.disabled
    alertScreenReader(`Job '${job.name}' ${job.disabled ? 'disabled' : 'enabled'}`)
    putFocusNextTick(`job-${job.key}-enabled`)
  })
}
</script>

<style scoped>
.job-name {
  background-color: rgba(var(--v-theme-tertiary), 0.7)
}
.progress-spinner-height {
  max-height: 64px;
  max-width: 64px;
  max-height: 64px;
  min-height: 64px;
}
</style>
