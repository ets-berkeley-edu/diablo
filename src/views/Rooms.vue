<template>
  <div v-if="!loading">
    <h2><v-icon class="pb-3" large>mdi-domain</v-icon> {{ rooms.length }} Capture-enabled Rooms</h2>
    <v-card outlined class="elevation-1">
      <div class="pt-6">
        <v-data-table
          hide-default-footer
          :items-per-page="rooms.length"
          :headers="headers"
          :items="rooms"
        >
          <template v-slot:body="{ items }">
            <tbody>
              <tr v-if="!items.length">
                <td>
                  No rooms found.
                </td>
              </tr>
              <tr v-for="item in items" :key="item.name">
                <td class="text-no-wrap">
                  <router-link :id="`room-${item.location}`" :to="`/room/${item.id}`">{{ item.location }}</router-link>
                </td>
                <td class="text-no-wrap">{{ item.capability }}</td>
              </tr>
            </tbody>
          </template>
        </v-data-table>
      </div>
    </v-card>
  </div>
</template>

<script>
  import {getAllRooms} from '@/api/berkeley'

  export default {
    name: 'Rooms',
    data: () => ({
      headers: [
        {text: 'Room', value: 'location'},
        {text: 'Capability', value: 'capability'}
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
