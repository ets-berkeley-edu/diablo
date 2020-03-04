<template>
  <div>
    <h1 v-if="!isLoading">{{ totalRoomCount }} Capture-enabled Rooms</h1>
    <v-data-table
      :headers="headers"
      :items="rooms"
      :items-per-page="100"
      :loading="isLoading"
      class="elevation-1"
    ></v-data-table>
  </div>
</template>

<script>

  import {getCaptureEnabledRooms} from "@/api/course-capture"

  export default {
    name: 'Home',
    data: () => ({
      headers: [
        {text: 'Building', value: 'building'},
        {text: 'Room', value: 'roomNumber', sortable: false},
        {text: 'Capabilities', value: 'capabilities'}
      ],
      isLoading: true,
      rooms: undefined,
      totalRoomCount: undefined
    }),
    created() {
      getCaptureEnabledRooms().then(data => {
        this.rooms = data['rooms']
        this.totalRoomCount = data['totalRoomCount']
        this.isLoading = false
      })
    }
  }
</script>
