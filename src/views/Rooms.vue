<template>
  <div v-if="!loading">
    <div class="pl-3">
      <h2><v-icon class="pb-1" large>mdi-domain</v-icon> {{ totalRoomCount }} Capture-enabled Rooms</h2>
    </div>
    <div class="pt-6">
      <v-data-table
        :headers="headers"
        :items="rooms"
        :items-per-page="100"
        :loading="loading"
        class="elevation-1"
      ></v-data-table>
    </div>
  </div>
</template>

<script>
  import Loading from '@/mixins/Loading'
  import {getCaptureEnabledRooms} from '@/api/capture'

  export default {
    name: 'Rooms',
    mixins: [Loading],
    data: () => ({
      headers: [
        {text: 'Building', value: 'building'},
        {text: 'Room', value: 'roomNumber', sortable: false},
        {text: 'Capabilities', value: 'capabilities'}
      ],
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
