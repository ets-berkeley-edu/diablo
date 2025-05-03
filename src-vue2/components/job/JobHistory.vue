<template>
  <v-card outlined class="elevation-1">
    <v-card-title class="align-start px-4 py-8">
      <div class="pt-2">
        <h2><v-icon class="pb-1" :color="$vuetify.theme.dark ? 'white' : 'primary'" large>mdi-history</v-icon> History</h2>
      </div>
      <v-spacer></v-spacer>
      <v-text-field
        v-if="$_.size(jobHistory)"
        v-model="search"
        append-icon="search"
        aria-label="Search Job History table"
        label="Search History"
        single-line
        hide-details
      ></v-text-field>
    </v-card-title>
    <v-data-table
      id="job-history"
      caption="Job History"
      :headers="headers"
      hide-default-footer
      hide-default-header
      :items="jobHistory"
      :loading="refreshing"
      no-data-text="Job history is empty"
      no-results-text="No matching jobs"
      :options="options"
      :page.sync="options.page"
      :search="search"
      @page-count="pageCount = $event"
    >
      <template #header="{props: {headers: columns}}">
        <thead>
          <tr>
            <th
              v-for="(column, colIndex) in columns"
              :id="`job-history-${column.value}-th`"
              :key="colIndex"
              class="text-start text-no-wrap"
              scope="col"
            >
              <span class="font-size-12 font-weight-bold">{{ column.text }}</span>
            </th>
          </tr>
        </thead>
      </template>
      <template #body="{items}">
        <tbody>
          <tr v-for="(item, index) in items" :key="index">
            <td :id="`job-history-${item.id}-jobKey`" columnheader="job-history-jobKey-th">
              {{ item.jobKey }}
            </td>
            <td :id="`job-history-${item.id}-failed`" columnheader="job-history-failed-th">
              <v-icon v-if="item.finishedAt" :color="item.failed ? 'red' : 'light-green'">
                {{ item.failed ? 'mdi-exclamation-thick' : 'mdi-check-bold' }}
              </v-icon>
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
              <span class="sr-only">Started </span>{{ item.startedAt | moment(dateFormat) }}
            </td>
            <td :id="`job-history-${item.id}-finishedAt`" columnheader="job-history-finishedAt-th">
              <span v-if="item.finishedAt"><span class="sr-only">Finished </span>{{ item.finishedAt | moment(dateFormat) }}</span>
            </td>
          </tr>
        </tbody>
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
  </v-card>
</template>

<script>
import Context from '@/mixins/Context'

export default {
  name: 'JobHistory',
  mixins: [Context],
  props: {
    jobHistory: {
      required: true,
      type: Array
    },
    refreshing: {
      required: true,
      type: Boolean
    }
  },
  data: () => ({
    dateFormat: 'dddd, MMMM Do, h:mm:ss a',
    headers: [
      {text: 'Key', value: 'jobKey'},
      {text: 'Status', value: 'failed'},
      {text: 'Started', value: 'startedAt'},
      {text: 'Finished', value: 'finishedAt'}
    ],
    options: {
      page: 1,
      itemsPerPage: 50
    },
    pageCount: undefined,
    richardPryor: false,
    search: undefined
  }),
  watch: {
    search(value) {
      this.richardPryor = value && value.toLowerCase() === 'the bed is on my foot'
    }
  }
}
</script>
