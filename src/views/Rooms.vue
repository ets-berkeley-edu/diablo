<template>
  <div>
    <div class="pl-3">
      <h2><v-icon class="pb-1" large>mdi-domain</v-icon> {{ rooms.length }} Capture-enabled Rooms</h2>
    </div>
    <div class="pt-6">
      <v-data-table
        hide-default-footer
        :headers="headers"
        :items="rooms"
        :items-per-page="100"
        outlined
        class="elevation-1"
      ></v-data-table>
    </div>
  </div>
</template>

<script>
  import {getAllRooms} from '@/api/report'

  export default {
    name: 'Rooms',
    data: () => ({
      headers: [
        {text: 'Building', value: 'building'},
        {text: 'Room', value: 'roomNumber', sortable: false},
        {text: 'Capabilities', value: 'capabilities'}
      ],
      rooms: undefined
    }),
    created() {
      getAllRooms().then(data => {
        this.rooms = data
        this.$ready()
      })
    }
  }
</script>
