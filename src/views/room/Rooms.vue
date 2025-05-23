<template>
  <v-card v-if="!contextStore.loading" class="border-sm">
    <v-card-title class="align-start">
      <v-row>
        <v-col class="pt-2" cols="12" md="6">
          <PageTitle :icon="mdiDomain" :text="`${size(rooms)} Rooms`" />
        </v-col>
        <v-col class="pr-4" cols="12" md="6">
          <v-tooltip v-model="adviseAgainstRoom237" color="pink" location="bottom">
            <template #activator="{attrs}">
              <v-text-field
                id="rooms-search-input"
                v-model="search"
                :append-icon="mdiMagnify"
                aria-label="Search rooms table"
                clearable
                hide-details
                label="Search"
                single-line
                v-bind="attrs"
              ></v-text-field>
            </template>
            Nothing. There ain't nothing in Room 237. But you ain't got no business going in there anyway. So stay out!
          </v-tooltip>
        </v-col>
      </v-row>
    </v-card-title>
    <v-data-table
      id="rooms-data-table"
      caption="Rooms"
      :headers="headers"
      :items="rooms"
      :items-per-page="itemsPerPage"
      no-results-text="No rooms"
      :page.sync="pageCurrent"
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
              :append-icon="getSortIcon(column)"
              :aria-label="`Sort by ${column.title} ${isSorted(column) && sortBy.order === 'asc' ? 'descending' : 'ascending'}`"
              class="font-size-12 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
              :class="{'icon-visible': isSorted(column)}"
              color="body"
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
        <tr v-for="(item, index) in items" :key="index">
          <td :id="`room-${item.id}-location`" columnheader="rooms-table-location-th">
            <router-link
              :id="`room-${item.id}`"
              class="text-anchor"
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
      <template #bottom={pageCount}>
        <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
          <v-pagination
            id="rooms-pagination"
            v-model="pageCurrent"
            :length="pageCount"
          ></v-pagination>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup>
import {alertScreenReader} from '@/lib/utils'
import {computed, onMounted, ref} from 'vue'
import {get, size, startsWith} from 'lodash'
import {mdiDomain, mdiMagnify} from '@mdi/js'
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

onMounted(() => {
  contextStore.loadingStart()
  getAllRooms().then(data => {
    rooms.value = data
    contextStore.loadingComplete('Rooms')
  })
})

const onUpdateSortBy = primarySortBy => {
  const key = get(primarySortBy, '0.key')
  pageCurrent.value = 1
  if (key) {
    const header = find(headers.value, {value: key})
    sortBy.value = primarySortBy[0]
    if (header) {
      alertScreenReader(`Sorted by ${header.title}, ${sortBy.value.order}ending`)
    }
  } else {
    sortBy.value = {key: '', order: ''}
    alertScreenReader('Unsorted')
  }
}
</script>
