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
          <tr v-if="!items.length">
            <td>
              No jobs found.
            </td>
          </tr>
          <tr v-for="job in items" :key="job.id">
            <td>
              <v-btn
                :id="`approve-${job.id}`"
                :aria-label="`Run ${job.id}`"
                color="primary"
                fab
                small
                dark
                @click="start(job.id)">
                <v-icon>mdi-video-plus</v-icon>
              </v-btn>
            </td>
            <td>
              {{ job.id }}
            </td>
            <td class="w-50">
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
        {text: 'Job'},
        {text: 'Name', value: 'id'},
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
      start(jobId) {
        startJob(jobId).then(() => {
          console.log('Job started')
        })
      }
    }
  }</script>
