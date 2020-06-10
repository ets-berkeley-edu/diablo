<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <h1><v-icon large>mdi-domain</v-icon> {{ $_.size(rooms) }} Rooms</h1>
      </div>
      <v-spacer></v-spacer>
      <v-tooltip v-model="adviseAgainstRoom237" bottom color="pink">
        <template v-slot:activator="{}">
          <v-text-field
            v-model="search"
            append-icon="mdi-magnify"
            label="Search"
            single-line
            hide-details
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
      <template v-slot:item.location="{ item }">
        <router-link :id="`room-${item.id}`" :to="`/room/${item.id}`">{{ item.location }}</router-link>
      </template>
      <template v-slot:item.kalturaResourceId="{ item }">
        {{ item.kalturaResourceId || '&mdash;' }}
      </template>
      <template v-slot:item.capabilityName="{ item }">
        {{ item.capability ? item.capabilityName : '&mdash;' }}
      </template>
      <template v-slot:item.isAuditorium="{ item }">
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
  import {getAllRooms} from '@/api/room'

  export default {
    name: 'Rooms',
    mixins: [Context],
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
