<template>
  <v-container v-if="!loading" class="pa-0" fluid>
    <v-card outlined class="elevation-1">
      <v-card-title>
        <PageTitle icon="mdi-video-off-outline" text="Blackouts" />
      </v-card-title>
      <v-card-text class="pb-0">
        <div>
          Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum
          sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies
          nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim.
        </div>
      </v-card-text>
      <v-card-title class="pb-0 pt-0">
        <v-spacer class="pb-0 pt-0 w-50"></v-spacer>
        <CreateBlackoutDialog :blackouts="blackouts" :on-close="onCloseDialog" />
      </v-card-title>
      <v-card-text>
        <div class="pt-8">
          <v-data-table
            disable-pagination
            disable-sort
            :headers="headers"
            hide-default-footer
            :items="blackouts"
            :loading="refreshing"
            no-results-text="No matching blackouts"
          >
            <template #body="{items}">
              <tbody>
                <tr v-if="!items.length">
                  <td colspan="6" class="py-4 subtitle-1">
                    No blackouts scheduled.
                  </td>
                </tr>
                <tr v-for="blackout in items" :key="blackout.id">
                  <td class="w-50">
                    {{ blackout.name }}
                  </td>
                  <td :id="`blackout-${blackout.id}-start-date`">
                    {{ blackout.startDate }}
                  </td>
                  <td :id="`blackout-${blackout.id}-end-date`">
                    {{ blackout.endDate }}
                  </td>
                  <td class="text-no-wrap">
                    {{ blackout.createdAt | moment('MMM DD, YYYY') }}
                  </td>
                  <td>
                    <v-btn
                      :id="`delete-blackout-${blackout.id}`"
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
      {text: 'Created', value: 'createdAt'},
      {text: 'Delete', class: 'pl-5 pr-0 mr-0'}
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
