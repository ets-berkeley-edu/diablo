<template>
  <div v-if="!loading">
    <h2><v-icon class="pb-3" large>mdi-domain</v-icon> {{ $_.size(rooms) }} Capture-enabled Rooms</h2>
    <v-card outlined class="elevation-1">
      <div class="pt-6">
        <v-card-title>
          <v-spacer></v-spacer>
          <v-text-field
            v-model="search"
            append-icon="mdi-magnify"
            label="Search"
            single-line
            hide-details
          ></v-text-field>
        </v-card-title>
        <v-data-table
          :headers="headers"
          hide-default-footer
          :items="rooms"
          no-results-text="No matching rooms"
          :options="options"
          :page.sync="options.page"
          :search="search"
          @page-count="pageCount = $event"
        >
          <template v-slot:body="{ items }">
            <tbody>
              <tr v-if="!items.length">
                <td>
                  No rooms found.
                </td>
              </tr>
              <tr v-for="room in items" :key="room.id">
                <td class="w-50">
                  <router-link :id="`room-${room.id}`" :to="`/room/${room.id}`">{{ room.location }}</router-link>
                </td>
                <td class="w-20">
                  {{ room.isAuditorium ? 'Yes' : 'No' }}
                </td>
                <td>
                  <SelectRoomCapability :options="capabilityOptions" :room="room" />
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
            total-visible="10"></v-pagination>
        </div>
      </div>
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import SelectRoomCapability from '@/components/room/SelectRoomCapability'
  import {getAllRooms, getCapabilityOptions} from '@/api/room'

  export default {
    name: 'Rooms',
    components: {SelectRoomCapability},
    mixins: [Context],
    data: () => ({
      capabilityOptions: undefined,
      headers: [
        {text: 'Room', value: 'location'},
        {text: 'Auditorium', value: 'isAuditorium'},
        {text: 'Capability', value: 'capability'}
      ],
      options: {
        page: 1,
        itemsPerPage: 50
      },
      pageCount: undefined,
      rooms: undefined,
      search: undefined
    }),
    mounted() {
      this.$loading()
      getAllRooms().then(data => {
        this.rooms = data
        getCapabilityOptions().then(options => {
          this.capabilityOptions = options
          this.$ready()
        })
      })
    }
  }
</script>
