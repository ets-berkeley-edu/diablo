<template>
  <v-select
    :id="id || `select-room-${room.id}-capability`"
    v-model="room.capability"
    dense
    item-text="label"
    item-value="value"
    :items="capabilityOptions"
    no-data-text="Select..."
    @change="update(room)"
  ></v-select>
</template>

<script>
  import {updateRoomCapability} from '@/api/berkeley'

  export default {
    name: 'SelectRoomCapability',
    props: {
      capabilityOptions: {
        required: true,
        type: Array
      },
      id: {
        required: false,
        type: String
      },
      room: {
        required: true,
        type: Object
      }
    },
    methods: {
      update(room) {
        updateRoomCapability(room.id, room.capability)
      }
    }
  }
</script>
