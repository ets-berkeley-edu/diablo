<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <h2><v-icon class="pb-3" large>mdi-wrench-outline</v-icon> Jobs</h2>
      </div>
      <v-spacer></v-spacer>
    </v-card-title>
    <v-data-table
      :headers="headers"
      hide-default-footer
      :items="jobs"
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
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getAvailableJobs, startJob} from '@/api/job'

  export default {
    name: 'Attic',
    mixins: [Context, Utils],
    data: () => ({
      headers: [
        {text: 'Job', class: 'w-10', sortable: false},
        {text: 'Key', value: 'key', sortable: false},
        {text: 'Description', value: 'description'}
      ],
      jobs: undefined
    }),
    mounted() {
      this.$loading()
      getAvailableJobs().then(data => {
        this.jobs = data
        this.$ready()
      }).catch(this.$ready)
    },
    methods: {
      start(jobKey) {
        startJob(jobKey).then(() => {
          console.log('Job started')
        })
      }
    }
  }
</script>
