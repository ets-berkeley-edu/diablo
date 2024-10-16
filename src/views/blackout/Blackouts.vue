<template>
  <v-container v-if="!loading" class="pa-0" fluid>
    <v-card outlined class="elevation-1">
      <v-card-title>
        <PageTitle icon="mdi-video-off-outline" text="Blackouts" />
      </v-card-title>
      <v-card-text class="pb-0">
        <div>
          The "Blackouts" job will delete Course Capture (Kaltura) events according to dates below.
        </div>
      </v-card-text>
      <v-card-title class="pb-0 pt-1">
        <v-spacer class="pb-0 pt-0 w-50"></v-spacer>
        <CreateBlackoutDialog :blackouts="blackouts" :on-close="onCloseDialog" />
      </v-card-title>
      <v-card-text>
        <div class="pt-8">
          <v-data-table
            caption="Blackouts"
            disable-pagination
            disable-sort
            :headers="headers"
            hide-default-footer
            hide-default-header
            :items="blackouts"
            :loading="refreshing"
            no-results-text="No matching blackouts"
          >
            <template #header="{props: {headers: columns}}">
              <thead>
                <tr>
                  <th
                    v-for="(column, colIndex) in columns"
                    :id="`blackouts-${column.value}-th`"
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
                <tr v-if="!items.length">
                  <td colspan="6" class="py-4 subtitle-1">
                    No blackouts scheduled.
                  </td>
                </tr>
                <tr v-for="blackout in items" :key="blackout.id">
                  <td :id="`blackout-${blackout.id}-name`" class="w-50" columnheader="blackouts-name-th">
                    {{ blackout.name }}
                  </td>
                  <td :id="`blackout-${blackout.id}-start-date`" columnheader="blackouts-startDate-th">
                    {{ blackout.startDate }}
                  </td>
                  <td :id="`blackout-${blackout.id}-end-date`" columnheader="blackouts-endDate-th">
                    {{ blackout.endDate }}
                  </td>
                  <td :id="`blackout-${blackout.id}-delete`" columnheader="blackouts-delete-th">
                    <v-btn
                      :id="`delete-blackout-${blackout.id}`"
                      :aria-label="`Delete ${blackout.name} Blackout`"
                      icon
                      @click="deleteBlackout(blackout.id)"
                    >
                      <v-icon>mdi-trash-can-outline</v-icon>
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </template>
          </v-data-table>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import Context from '@/mixins/Context'
import CreateBlackoutDialog from '@/components/util/CreateBlackoutDialog'
import PageTitle from '@/components/util/PageTitle'
import Utils from '@/mixins/Utils'
import {deleteBlackout, getAllBlackouts} from '@/api/blackout'

export default {
  name: 'Blackouts',
  mixins: [Context, Utils],
  components: {CreateBlackoutDialog, PageTitle},
  data: () => ({
    blackouts: undefined,
    headers: [
      {text: 'Name', value: 'name'},
      {text: 'Start Date', value: 'startDate'},
      {text: 'End Date', value: 'endDate'},
      {text: 'Delete', class: 'pl-5 pr-0 mr-0', value: 'delete'}
    ],
    refreshing: false
  }),
  created() {
    this.$loading()
    this.refresh().then(() => {
      this.$ready('Blackouts')
    })
  },
  methods: {
    deleteBlackout(blackoutId) {
      this.refreshing = true
      deleteBlackout(blackoutId).then(() => {
        this.refresh().then(() => {
          this.alertScreenReader('Blackout deleted.')
          this.refreshing = false
        })
      })
    },
    onCloseDialog(refreshBlackouts) {
      if (refreshBlackouts) {
        this.refresh()
      }
    },
    refresh() {
      this.refreshing = true
      return getAllBlackouts().then(data => {
        this.blackouts = data
        this.refreshing = false
      })
    }
  }
}
</script>
