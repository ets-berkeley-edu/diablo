<template>
  <div>
    <h1 v-if="!loading">{{ totalRoomCount }} Capture-enabled Rooms</h1>
    <v-data-table
      :headers="headers"
      :items="rooms"
      :items-per-page="100"
      :loading="loading"
      class="elevation-1"
    ></v-data-table>
  </div>
</template>

<script>
  import Loading from '@/mixins/Loading'
  import {getCaptureEnabledRooms} from '@/api/capture'

  export default {
    name: 'Admin',
    mixins: [Loading],
    data: () => ({
      headers: [
        {text: 'Building', value: 'building'},
        {text: 'Room', value: 'roomNumber', sortable: false},
        {text: 'Capabilities', value: 'capabilities'}
      ],
      rooms: undefined,
      totalRoomCount: undefined
    }),
    created() {
      getCaptureEnabledRooms().then(data => {
        this.rooms = data['rooms']
        this.totalRoomCount = data['totalRoomCount']
        this.loaded()
      })
    }
  }
</script>
