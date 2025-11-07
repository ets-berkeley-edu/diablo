<template>
  <v-card v-if="!contextStore.loading" elevation="0">
    <v-card-title>
      <PageTitle :icon="mdiVideoOffOutline" text="Blackouts" />
    </v-card-title>
    <v-card-subtitle class="font-size-18">
      The "Blackouts" job will delete Course Capture (Kaltura) events according to dates below.
    </v-card-subtitle>
    <v-card-text>
      <div class="d-flex justify-end pa-3">
        <CreateBlackoutDialog :blackouts="blackouts" :on-close="onCloseDialog" />
      </div>
      <v-data-table
        :class="{'v-table-padding-override': blackouts.length}"
        disable-sort
        :headers="headers"
        hide-default-footer
        :items="blackouts"
        :items-per-page="-1"
        :loading="isRefreshing"
      >
        <template #headers="{columns}">
          <tr>
            <th
              v-for="(column, colIndex) in columns"
              :id="`blackouts-${column.value}-th`"
              :key="colIndex"
              class="font-size-13 font-weight-bold text-medium-emphasis text-no-wrap"
              :class="column.class"
              scope="col"
            >
              {{ column.title }}
            </th>
          </tr>
        </template>
        <template #body="{items}">
          <tr v-if="!isRefreshing && !items.length">
            <td class="py-4 text-center text-subtitle-1" :colspan="headers.length">
              No blackouts scheduled.
            </td>
          </tr>
          <tr v-for="blackout in items" :key="blackout.id">
            <td :id="`blackout-${blackout.id}-name`" class="font-size-16 w-50" columnheader="blackouts-name-th">
              {{ blackout.name }}
            </td>
            <td :id="`blackout-${blackout.id}-start-date`" class="font-size-16 text-no-wrap" columnheader="blackouts-startDate-th">
              {{ blackout.startDate }}
            </td>
            <td :id="`blackout-${blackout.id}-end-date`" class="font-size-16 text-no-wrap" columnheader="blackouts-endDate-th">
              {{ blackout.endDate }}
            </td>
            <td :id="`blackout-${blackout.id}-delete`" class="font-size-16 text-center" columnheader="blackouts-delete-th">
              <v-btn
                :id="`delete-blackout-${blackout.id}`"
                :aria-label="`Delete ${blackout.name} Blackout`"
                color="red"
                :icon="mdiTrashCan"
                title="Delete"
                variant="text"
                @click="onClickDelete(blackout)"
              />
            </td>
          </tr>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import {mdiTrashCan, mdiVideoOffOutline} from '@mdi/js'
import {onMounted, ref} from 'vue'
import CreateBlackoutDialog from '@/components/util/CreateBlackoutDialog'
import PageTitle from '@/components/util/PageTitle'
import {alertScreenReader} from '@/lib/utils'
import {deleteBlackout, getAllBlackouts} from '@/api/blackout'
import {useContextStore} from '@/stores/context'

const blackouts = ref([])
const contextStore = useContextStore()
const headers = [
  {title: 'Name', value: 'name'},
  {title: 'Start Date', value: 'startDate'},
  {title: 'End Date', value: 'endDate'},
  {title: 'Delete', class: 'text-center', value: 'delete'}
]
const isRefreshing = ref(false)

contextStore.loadingStart()

onMounted(() => {
  refresh().then(() => {
    contextStore.loadingComplete()
  })
})

const onClickDelete = blackout => {
  const deletedName = blackout.name
  isRefreshing.value = true
  deleteBlackout(blackout.id).then(() => {
    refresh().then(() => {
      alertScreenReader(`Deleted blackout: ${deletedName}`)
      isRefreshing.value = false
    })
  })
}

const onCloseDialog = refreshBlackouts => {
  if (refreshBlackouts) {
    refresh()
  }
}

const refresh = () => {
  isRefreshing.value = true
  return getAllBlackouts().then(data => {
    blackouts.value = data
    isRefreshing.value = false
  })
}
</script>
