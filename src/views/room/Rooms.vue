<template>
  <v-card v-if="!contextStore.loading" class="border-sm">
    <v-card-title class="align-start">
      <v-row>
        <v-col class="pt-2" cols="12" md="6">
          <PageTitle :icon="mdiDomain" :text="`${size(rooms)} Rooms`" />
        </v-col>
        <v-col class="pr-4" cols="12" md="6">
          <v-tooltip v-model="adviseAgainstRoom237" class="tooltip" location="bottom">
            <template #activator="{props: tooltipProps}">
              <v-text-field
                id="rooms-search-input"
                v-model="search"
                :append-icon="mdiMagnify"
                :aria-describedby="undefined"
                aria-label="Search rooms table"
                clearable
                hide-details
                label="Search"
                single-line
                v-bind="tooltipProps"
              />
            </template>
            <span class="font-size-16">Nothing. There ain't nothing in Room 237. But you ain't got no business going in there anyway. So stay out!</span>
          </v-tooltip>
        </v-col>
      </v-row>
    </v-card-title>
    <v-data-table
      id="rooms-data-table"
      v-model:page="pageCurrent"
      :headers="headers"
      :items="rooms"
      :items-per-page="itemsPerPage"
      :search="search"
      :sort-by="[sortBy]"
      @update:sort-by="onUpdateSortBy"
    >
      <template #headers="{columns, isSorted, toggleSort, getSortIcon}">
        <tr>
          <th
            v-for="(column, index) in columns"
            :id="`rooms-table-${column.value}-th`"
            :key="index"
            :aria-label="column.title"
            :aria-sort="isSorted(column) ? `${sortBy.order}ending` : null"
            class="text-start"
            scope="col"
          >
            <v-btn
              :id="`rooms-table-sort-by-${column.value}-btn`"
              :append-icon="isSorted(column) ? getSortIcon(column) : undefined"
              :aria-label="sortButtonAriaLabel(column, isSorted)"
              class="font-size-13 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
              :class="{'icon-visible': isSorted(column)}"
              density="compact"
              variant="plain"
              @click="() => toggleSort(column)"
            >
              {{ column.title }}
            </v-btn>
          </th>
        </tr>
      </template>
      <template #body="{items}">
        <tr v-if="!items.length">
          <td class="py-5 text-center text-subtitle-1" :colspan="headers.length">
            No rooms.
          </td>
        </tr>
        <tr v-for="(item, index) in items" :key="index">
          <td :id="`room-${item.id}-location`" columnheader="rooms-table-location-th">
            <router-link
              :id="`room-${item.id}`"
              :to="`/room/${item.id}`"
            >
              {{ item.location }}
            </router-link>
          </td>
          <td :id="`room-${item.id}-kalturaResourceId`" columnheader="rooms-table-kalturaResourceId-th">
            <span aria-hidden="true">{{ item.kalturaResourceId || '&mdash;' }}</span>
            <span class="sr-only">{{ item.kalturaResourceId || 'blank' }}</span>
          </td>
          <td :id="`room-${item.id}-capability`" columnheader="rooms-table-capability-th">
            <span aria-hidden="true">{{ item.capability ? item.capabilityName : '&mdash;' }}</span>
            <span class="sr-only">{{ item.capability ? item.capabilityName : 'blank' }}</span>
          </td>
          <td :id="`room-${item.id}-isAuditorium`" columnheader="rooms-table-isAuditorium-th">
            {{ item.isAuditorium ? 'Yes' : 'No' }}
          </td>
        </tr>
      </template>
      <template #bottom="{pageCount}">
        <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
          <v-pagination
            id="rooms-pagination"
            v-model="pageCurrent"
            :length="pageCount"
          />
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {find, get, size, startsWith} from 'lodash'
import {mdiDomain, mdiMagnify} from '@mdi/js'
import {alertScreenReader} from '@/lib/utils'
import PageTitle from '@/components/util/PageTitle'
import {getAllRooms} from '@/api/room'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const headers = [
  {title: 'Room', value: 'location', class: 'w-50', sortable: true},
  {title: 'Kaltura Resource', value: 'kalturaResourceId', class: 'w-20', sortable: true},
  {title: 'Capability', value: 'capabilityName', class: 'w-20', sortable: true},
  {title: 'Auditorium', value: 'isAuditorium', class: 'w-10', sortable: true}
]
const itemsPerPage = 50
const pageCurrent = ref(1)
const rooms = ref([])
const search = ref(undefined)
const sortBy = ref({key: '', order: ''})

const adviseAgainstRoom237 = computed(() => {
  return startsWith(search.value, '237 ') && size(search.value) < 6
})

contextStore.loadingStart()

onMounted(() => {
  getAllRooms().then(data => {
    rooms.value = data
    contextStore.loadingComplete()
  })
})

const onUpdateSortBy = primarySortBy => {
  const key = get(primarySortBy, '0.key')
  pageCurrent.value = 1
  if (key) {
    const header = find(headers, {value: key})
    sortBy.value = primarySortBy[0]
    if (header) {
      alertScreenReader(`Sorted by ${header.title}, ${sortBy.value.order}ending`)
    }
  } else {
    sortBy.value = {key: '', order: ''}
    alertScreenReader('Default sort order restored')
  }
}

const sortButtonAriaLabel = (column, isSorted) => {
  if (isSorted(column) && 'desc' === sortBy.value.order) {
    return 'Restore default sort order'
  } else {
    return `Sort by ${column.title} ${isSorted(column) && sortBy.value.order === 'asc' ? 'descending' : 'ascending'}`
  }
}
</script>

<style>
.v-tooltip > .v-overlay__content {
  background-color: rgb(var(--v-theme-accent)) !important;
}
</style>
