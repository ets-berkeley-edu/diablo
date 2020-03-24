<template>
  <div v-if="!loading">
    <h2><v-icon class="pb-3" large>mdi-domain</v-icon> {{ rooms.length }} Capture-enabled Rooms</h2>
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
          :loading="isFetching"
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
              <tr v-for="item in items" :key="item.name">
                <td class="w-50">
                  <router-link :id="`room-${item.location}`" :to="`/room/${item.id}`">{{ item.location }}</router-link>
                </td>
                <td class="w-50">
                  <v-select
                    :id="`select-room-${item.id}-capability`"
                    v-model="item.capability"
                    dense
                    item-text="label"
                    item-value="value"
                    :items="capabilityOptions"
                    no-data-text="Select..."
                    @change="updateCapability(item)"
                  ></v-select>
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
  import {getAllRooms, getCapabilityOptions, updateRoomCapability} from '@/api/berkeley'

  export default {
    name: 'Rooms',
    mixins: [Context],
    data: () => ({
      capabilityOptions: undefined,
      headers: [
        {text: 'Room', value: 'location'},
        {text: 'Capability', value: 'capability'}
      ],
      isFetching: true,
      options: {
        page: 1,
        itemsPerPage: 50
      },
      pageCount: undefined,
      rooms: undefined,
      search: undefined
    }),
    mounted() {
      this.isFetching = true
      getAllRooms().then(data => {
        this.rooms = data
        this.isFetching = false
        getCapabilityOptions().then(options => {
          this.capabilityOptions = options
          this.capabilityOptions.unshift({
            'label': 'None',
            'value': null,
          })
        })
        this.$ready()
      })
    },
    methods: {
      updateCapability(room) {
        updateRoomCapability(room.id, room.capability)
      }
    }
  }
</script>
