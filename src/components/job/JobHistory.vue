<template>
  <v-card class="border-sm">
    <v-card-title>
      <v-row>
        <v-col cols="12" sm="5">
          <h2 id="job-history-header" class="my-2">
            <v-icon
              class="pb-1"
              :color="$vuetify.theme.dark ? 'white' : 'primary'"
              :icon="mdiHistory"
              large
            /> History
          </h2>
        </v-col>
        <v-col cols="12" sm="7">
          <v-text-field
            v-if="size(jobHistory)"
            id="search-job-history-input"
            v-model="search"
            :append-icon="mdiMagnify"
            :aria-describedby="undefined"
            aria-label="Search Job History table"
            class="my-2"
            label="Search History"
            single-line
            hide-details
          ></v-text-field>
        </v-col>
      </v-row>
    </v-card-title>
    <v-data-table
      id="job-history-table"
      :headers="headers"
      hide-default-footer
      :items="jobHistory"
      :items-per-page="itemsPerPage"
      :loading="refreshing"
      no-data-text="Job history is empty"
      no-results-text="No matching jobs"
      :page.sync="pageCurrent"
      :search="search"
    >
      <template #headers="{columns}">
        <tr>
          <th
            v-for="(column, colIndex) in columns"
            :id="`job-history-${column.value}-th`"
            :key="colIndex"
            class="font-size-12 font-weight-bold text-medium-emphasis text-no-wrap"
            scope="col"
          >
            {{ column.title }}
          </th>
        </tr>
      </template>
      <template #body="{items}">
        <tr v-for="(item, index) in items" :key="index">
          <td :id="`job-history-${item.id}-jobKey`" columnheader="job-history-jobKey-th">
            {{ item.jobKey }}
          </td>
          <td :id="`job-history-${item.id}-failed`" columnheader="job-history-failed-th">
            <v-icon
              v-if="item.finishedAt"
              :color="item.failed ? 'red' : 'light-green'"
              :icon="item.failed ? mdiExclamationThick : mdiCheckBold"
              :title="`${item.jobKey} job ${item.failed ? 'failed' : 'finished'}`"
            />
            <span v-if="item.finishedAt" class="sr-only">{{ item.failed ? `${item.jobKey} job failed` : `${item.jobKey} job finished` }}</span>
            <v-progress-circular
              v-if="!item.finishedAt"
              :aria-label="`${item.jobKey} job is running`"
              :indeterminate="true"
              rotate="5"
              size="24"
              width="4"
              color="orange"
            ></v-progress-circular>
          </td>
          <td :id="`job-history-${item.id}-startedAt`" columnheader="job-history-startedAt-th">
            <span class="sr-only">Started </span>{{ formatDate(item.startedAt) }}
          </td>
          <td :id="`job-history-${item.id}-finishedAt`" columnheader="job-history-finishedAt-th">
            <span v-if="item.finishedAt"><span class="sr-only">Finished </span>{{ formatDate(item.finishedAt) }}</span>
          </td>
        </tr>
      </template>
      <template #bottom={pageCount}>
        <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
          <v-pagination
            id="rooms-pagination"
            v-model="pageCurrent"
            :length="pageCount"
            total-visible="10"
          ></v-pagination>
        </div>
      </template>
    </v-data-table>
    <v-bottom-sheet v-model="richardPryor">
      <v-sheet class="text-center" dark height="800px">
        <v-btn
          id="get-the-damn-bed-off-my-foot"
          class="mt-6"
          color="primary"
          @click="() => richardPryor = !richardPryor"
        >
          Close
        </v-btn>
        <div class="py-3">
          <img alt="The bed is on my foot!" src="@/assets/the-bed-is-on-my-foot.jpg">
        </div>
      </v-sheet>
    </v-bottom-sheet>
  </v-card>
</template>

<script setup>
import {computed, ref, watch} from 'vue'
import {DateTime} from 'luxon'
import {mdiCheckBold, mdiExclamationThick, mdiHistory, mdiMagnify} from '@mdi/js'
import {size} from 'lodash'

const props = defineProps({
  jobHistory: {
    required: true,
    type: Array
  },
  refreshing: {
    required: true,
    type: Boolean
  }
})

const headers = [
  {title: 'Key', value: 'jobKey'},
  {title: 'Status', value: 'failed'},
  {title: 'Started', value: 'startedAt'},
  {title: 'Finished', value: 'finishedAt'}
]
const itemsPerPage = 50
const pageCurrent = ref(1)
const richardPryor = ref(false)
const search = ref('')

watch(search, input => {
  if (input && input.length && input.toLowerCase() === 'the bed is on my foot') {
    richardPryor.value = true
  }
})

const formatDate = date => {
  return DateTime.fromISO(date).toLocaleString({...DateTime.DATETIME_MED_WITH_WEEKDAY, weekday: 'long'})
}
</script>
