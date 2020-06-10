<template>
  <v-card outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <h2><v-icon class="pb-1" large>mdi-history</v-icon> History</h2>
      </div>
      <v-spacer></v-spacer>
      <v-text-field
        v-if="$_.size(jobHistory)"
        v-model="search"
        append-icon="search"
        label="Search History"
        single-line
        hide-details
      ></v-text-field>
    </v-card-title>
    <v-data-table
      :headers="headers"
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
  import {getJobHistory} from '@/api/job'

  export default {
    name: 'JobHistory',
    mixins: [Context],
    props: {
      ping: {
        default: undefined,
        required: false,
        type: Number
      }
    },
    data: () => ({
      dateFormat: 'dddd, MMMM Do, h:mm:ss a',
      daysCount: 3,
      headers: [
        {text: 'Key', value: 'jobKey'},
        {text: 'Status', value: 'failed'},
        {text: 'Started', value: 'startedAt'},
        {text: 'Finished', value: 'finishedAt'}
      ],
      jobHistory: undefined,
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
      ping(value) {
        if (value && !this.refreshing) {
          this.refresh()
        }
      },
      search(value) {
        this.richardPryor = value && value.toLowerCase() === 'the bed is on my foot'
      }
    },
    created() {
      this.refresh()
    },
    destroyed() {
      clearTimeout(this.refresher)
    },
    methods: {
      refresh() {
        this.refreshing = true
        return getJobHistory(this.daysCount).then(data => {
          this.jobHistory = data
          this.refreshing = false
          if (!this.loading) {
            this.alertScreenReader('Job History refreshed')
          }
          this.scheduleRefresh()
        })
      },
      scheduleRefresh() {
        // Clear previous job, if pending
        clearTimeout(this.refresher)
        this.refresher = setTimeout(this.refresh, 5000)
      }
    }
  }
</script>
