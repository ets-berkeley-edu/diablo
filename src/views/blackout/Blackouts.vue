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
        <div>
          TODO: link to create page
        </div>
      </v-card-title>
      <v-card-text>
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
                <td colspan="6" class="pt-4 subtitle-1">
                  You have no blackouts.
                </td>
              </tr>
              <tr v-for="blackout in items" :key="blackout.id">
                <td>
                  <router-link :id="`blackout-${blackout.id}`" :to="`/blackout/${blackout.id}`">{{ blackout.name }}</router-link>
                </td>
                <td :id="`blackout-${blackout.id}-start-date`" class="w-50">
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
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import Context from '@/mixins/Context'
import PageTitle from '@/components/util/PageTitle'
import Utils from '@/mixins/Utils'
import {deleteBlackout, getAllBlackouts} from '@/api/blackout'

export default {
  name: 'Blackouts',
  mixins: [Context, Utils],
  components: {PageTitle},
  data: () => ({
    headers: [
      {text: 'Name', value: 'name'},
      {text: 'Start Date', value: 'startDate'},
      {text: 'End Date', value: 'endDate'},
      {text: 'Created', value: 'createdAt'},
      {text: 'Delete', class: 'pl-5 pr-0 mr-0'}
    ],
    blackouts: undefined,
    refreshing: false
  }),
  mounted() {
    this.$loading()
    this.loadAllBlackouts().then(() => {
      this.$ready('Blackouts')
    })
  },
  methods: {
    createBlackout() {
      this.goToPath('/blackout')
    },
    deleteBlackout(blackoutId) {
      this.refreshing = true
      deleteBlackout(blackoutId).then(() => {
        this.alertScreenReader('Blackout deleted.')
        this.loadAllBlackouts().then(() => {
          this.refreshing = false
        })
      })
    },
    loadAllBlackouts() {
      return getAllBlackouts().then(data => {
        this.blackouts = data
      })
    }
  }
}
</script>
