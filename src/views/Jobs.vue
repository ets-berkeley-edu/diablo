<template>
  <div v-if="!contextStore.loading">
    <v-card class="mb-4" elevation="0">
      <v-card-title>
        <PageTitle
          :icon="mdiHandsPray"
          sub-title="A sacred place for Admin users."
          text="The Chancel"
        />
      </v-card-title>
      <v-card-text class="px-0">
        <v-data-table
          id="job-schedule-table"
          :class="{'v-table-padding-override': jobSchedule.jobs.length}"
          disable-sort
          :headers="headers"
          hide-default-footer
          :items="jobSchedule.jobs"
          :items-per-page="-1"
        >
          <template #headers="{columns}">
            <tr>
              <th
                v-for="(column, colIndex) in columns"
                :id="`job-schedule-${column.value}-th`"
                :key="colIndex"
                class="font-size-13 font-weight-bold text-medium-emphasis text-no-wrap"
                scope="col"
              >
                <span :class="`${column.class} ${column.value === 'schedule' ? 'pl-2' : ''}`">{{ column.title }}</span>
              </th>
            </tr>
          </template>
          <template #body="{items}">
            <tr v-if="!items.length">
              <td id="job-schedule-no-data" class="py-5 text-center text-subtitle-1" :colspan="headers.length">
                No jobs.
              </td>
            </tr>
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
                    class="my-1"
                    :disabled="isRunning(job.key)"
                    icon
                    size="large"
                    @click="runJob(job)"
                  >
                    <v-icon
                      v-if="!isRunning(job.key)"
                      color="success"
                      :icon="mdiPlay"
                      size="36"
                    />
                    <v-progress-circular
                      v-if="isRunning(job.key)"
                      :aria-label="`${job.name} job is running`"
                      color="success"
                      indeterminate
                      size="56"
                      width="8"
                    />
                  </v-btn>
                </div>
              </td>
              <td
                :id="`job-schedule-${job.key}-name`"
                class="bg-tertiary text-no-wrap"
                columnheader="job-schedule-name-th"
              >
                <span class="font-weight-bold font-size-16">{{ job.name }}</span>
              </td>
              <td
                :id="`job-schedule-${job.key}-description`"
                class="pb-2 pt-2"
                columnheader="job-schedule-description-th"
              >
                <span v-html="job.description" />
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
                  />
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
                  <v-icon class="mx-4" color="error" :icon="mdiAlert" />
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
                  :aria-describedby="undefined"
                  aria-label="Schedule Type"
                  autocomplete="off"
                  hide-details
                  item-props
                  :items="scheduleTypeOptions"
                  label="Type"
                  :list-props="{ariaLabel: 'Schedule type', ariaLive: 'off', id: 'schedule-type-list'}"
                  :menu-props="{attach: menuContainer, eager: true, id: 'schedule-type-menu'}"
                  :title="undefined"
                  :value="get(find(scheduleTypeOptions, {value: editJob.schedule.type}), 'title')"
                  @update:menu="onToggleScheduleTypeMenu"
                  @update:model-value="editJob.schedule.value = ''"
                />
                <div id="schedule-type-menu-container" ref="menuContainer" />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  id="schedule-value-input"
                  v-model="editJob.schedule.value"
                  :label="editJob.schedule.type === 'day_at' ? 'Time' : 'Duration'"
                  required
                  :suffix="editJob.schedule.type === 'day_at' ? 'UTC' : ''"
                  :type="editJob.schedule.type === 'day_at' ? 'time' : 'number'"
                />
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <ProgressButton
            id="edit-schedule-save-btn"
            :action="scheduleEditSave"
            :aria-label="`${isSavingJob ? 'Saving' : 'Save'} ${get(editJob, 'name')} job schedule`"
            :disabled="disableScheduleSave"
            :in-progress="isSavingJob"
            :text="isSavingJob ? 'Saving' : 'Save'"
          />
          <v-btn
            id="edit-schedule-cancel-btn"
            :aria-label="`Cancel edit ${get(editJob, 'name')} job schedule`"
            class="ml-2"
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
import {DateTime} from 'luxon'
import {mdiAlert, mdiHandsPray, mdiPlay, mdiPlaylistEdit} from '@mdi/js'
import {onBeforeUnmount, onMounted, ref, watch} from 'vue'
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
const menuContainer = ref()
const refresher = ref()
const refreshing = ref(false)
const scheduleTypeOptions = [
  {id: 'schedule-type-day_at', role: 'option', title: 'Day at', value: 'day_at'},
  {id: 'schedule-type-minutes', role: 'option', title: 'Minutes', value: 'minutes'},
  {id: 'schedule-type-seconds', role: 'option', title: 'Seconds', value: 'seconds'},
]

watch(editJob, job => {
  // deep: true,
  disableScheduleSave.value = !get(job, 'schedule.value') || parseInt(job.schedule.value) < 0
})

contextStore.loadingStart()

onMounted(() => {
  getJobSchedule().then(data => {
    jobSchedule.value = data
    refresh().then(() => {
      contextStore.loadingComplete()
    })
  })
})

onBeforeUnmount(() => {
  clearTimeout(refresher.value)
})

const isRunning = (jobKey) => {
  return !!find(jobHistory.value, h => h.jobKey === jobKey && !h.finishedAt)
}

const onToggleScheduleTypeMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick('schedule-type-day_at')
  }
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
    startedAt: DateTime.now().toISO()
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
.progress-spinner-height {
  max-height: 64px;
  max-width: 64px;
  max-height: 64px;
  min-height: 64px;
}
</style>
