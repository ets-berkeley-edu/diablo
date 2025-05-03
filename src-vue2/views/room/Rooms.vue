<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <PageTitle icon="mdi-domain" :text="`${$_.size(rooms)} Rooms`" />
      <v-spacer></v-spacer>
      <v-tooltip v-model="adviseAgainstRoom237" bottom color="pink">
        <template #activator="{attrs}">
          <v-text-field
            v-model="search"
            append-icon="mdi-magnify"
            aria-label="Search rooms table"
            label="Search"
            single-line
            hide-details
            v-bind="attrs"
          ></v-text-field>
        </template>
        Nothing. There ain't nothing in Room 237. But you ain't got no business going in there anyway. So stay out!
      </v-tooltip>
    </v-card-title>
    <v-data-table
      id="rooms-data-table"
      caption="Rooms"
      :headers="headers"
      hide-default-footer
      hide-default-header
      :items="rooms"
      no-results-text="No rooms"
      :options="options"
      :page.sync="options.page"
      :search="search"
      @page-count="pageCount = $event"
    >
      <template #header="{props: {headers: columns, options: {sortBy, sortDesc}}, on: {sort}}">
        <thead>
          <tr>
            <th
              v-for="(column, index) in columns"
              :id="`rooms-table-${column.value}-th`"
              :key="index"
              :aria-label="column.text"
              :aria-sort="getAriaSortIndicator(column, sortBy, sortDesc)"
              class="text-start"
              :class="{'sortable': column.sortable === false}"
              scope="col"
            >
              <v-btn
                :id="`rooms-table-sort-by-${column.value}-btn`"
                :aria-label="getSortButtonAriaLabel(column, sortBy, sortDesc)"
                class="font-size-12 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
                :class="{'icon-visible': sortBy[0] === column.value}"
                color="white"
                density="compact"
                plain
                @click="() => onClickSort(column, sort, sortBy, sortDesc)"
              >
                {{ column.text }}
                <v-icon :aria-hidden="true" small right>{{ getSortByIcon(column, sortBy, sortDesc) }}</v-icon>
              </v-btn>
            </th>
          </tr>
        </thead>
      </template>
      <template #body="{items}">
        <tbody>
          <tr v-for="(item, index) in items" :key="index">
            <td :id="`room-${item.id}-location`" columnheader="rooms-table-location-th">
              <router-link :id="`room-${item.id}`" :to="`/room/${item.id}`">{{ item.location }}</router-link>
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
  </v-card>
</template>

<script>
import Context from '@/mixins/Context'
import PageTitle from '@/components/util/PageTitle'
import {getAllRooms} from '@/api/room'

export default {
  name: 'Rooms',
  mixins: [Context],
  components: {PageTitle},
  data: () => ({
    headers: [
      {text: 'Room', value: 'location', class: 'w-50'},
      {text: 'Kaltura Resource', value: 'kalturaResourceId', class: 'w-20'},
      {text: 'Capability', value: 'capabilityName', class: 'w-20'},
      {text: 'Auditorium', value: 'isAuditorium', class: 'w-10'}
    ],
    options: {
      page: 1,
      itemsPerPage: 50
    },
    pageCount: undefined,
    rooms: undefined,
    search: undefined
  }),
  computed: {
    adviseAgainstRoom237() {
      return this.$_.startsWith(this.search, '237 ') && this.$_.size(this.search) < 6
    }
  },
  mounted() {
    this.$loading()
    getAllRooms().then(data => {
      this.rooms = data
      this.$ready('Rooms')
    })
  },
  methods: {
    getAriaSortIndicator(column, sortBy, sortDesc) {
      if (column.value && sortBy[0] === column.value) {
        return sortDesc[0] ? 'descending' : 'ascending'
      } else {
        return undefined
      }
    },
    getSortButtonAriaLabel(column, sortBy, sortDesc) {
      let label = `${column.text}: `
      if (sortBy[0] === column.value) {
        label += `sorted ${sortDesc[0] ? 'descending' : 'ascending'}.`
        label += ` Activate to sort ${sortDesc[0] ? 'ascending' : 'descending'}.`
      } else {
        label += 'not sorted. Activate to sort ascending.'
      }
      return label
    },
    getSortByIcon(column, sortBy, sortDesc) {
      return sortBy[0] === column.value && sortDesc[0] ? 'mdi-arrow-down' : 'mdi-arrow-up'
    },
    onClickSort(column, sort, sortBy, sortDesc) {
      const sortDirection = this.$_.first(sortBy) === column.value && !sortDesc[0] ? 'descending' : 'ascending'
      sort(column.value)
      this.alertScreenReader(`Sorted by ${column.text}, ${sortDirection}`)
      this.$putFocusNextTick(`rooms-table-sort-by-${column.value}-btn`)
    }
  }
}
</script>
