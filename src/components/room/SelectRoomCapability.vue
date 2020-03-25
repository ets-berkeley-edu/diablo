<template>
  <v-select
    :id="id || `select-room-${room.id}-capability`"
    v-model="room.capability"
    dense
    item-text="text"
    item-value="value"
    :items="capabilityOptions"
    no-data-text="Select..."
    @change="update(room)"
  ></v-select>
</template>

<script>
  import {updateRoomCapability} from '@/api/room'

  export default {
    name: 'SelectRoomCapability',
    props: {
      options: {
        required: true,
        type: Object
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
    data: () => ({
      capabilityOptions: [{
        'text': 'None',
        'value': null,
      }]
    }),
    created() {
      this.$_.each(this.options, (text, value) => {
        this.capabilityOptions.push({text, value})
      })
    },
    methods: {
      update(room) {
        updateRoomCapability(room.id, room.capability)
      }
    }
  }
</script>
