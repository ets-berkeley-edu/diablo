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
      :headers="headers"
      hide-default-footer
      :items="rooms"
      no-results-text="No rooms"
      :options="options"
      :page.sync="options.page"
      :search="search"
      @page-count="pageCount = $event"
    >
      <template #item.location="{item}">
        <router-link :id="`room-${item.id}`" :to="`/room/${item.id}`">{{ item.location }}</router-link>
      </template>
      <template #item.kalturaResourceId="{item}">
        {{ item.kalturaResourceId || '&mdash;' }}
      </template>
      <template #item.capabilityName="{item}">
        {{ item.capability ? item.capabilityName : '&mdash;' }}
      </template>
      <template #item.isAuditorium="{item}">
        {{ item.isAuditorium ? 'Yes' : 'No' }}
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
  }
}
</script>
