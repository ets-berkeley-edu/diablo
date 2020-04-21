<template>
  <v-select
    :id="`select-room-capability-${room.id}`"
    v-model="capability"
    dense
    :item-disabled="disableRoomCapability"
    item-text="text"
    item-value="value"
    :items="capabilityOptions"
    no-data-text="Select..."
    @change="updateCapability()"
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
      isAuditorium: {
        required: true,
        type: Boolean
      },
      onUpdate: {
        required: true,
        type: Function
      },
      room: {
        required: true,
        type:Object
      }
    },
    data: () => ({
      capability: null,
      capabilityOptions: [{
        'text': 'None',
        'value': null,
      }]
    }),
    watch: {
      isAuditorium(value) {
        if (!value && this.capability === 'screencast_and_video') {
          this.capability = null
          this.updateCapability()
        }
      }
    },
    created() {
      this.capability = this.room.capability
      this.$_.each(this.options, (text, value) => {
        this.capabilityOptions.push({text, value})
      })
    },
    methods: {
      disableRoomCapability(capability) {
        return capability.value === 'screencast_and_video' && !this.isAuditorium
      },
      updateCapability() {
        updateRoomCapability(this.room.id, this.capability).then(this.onUpdate(this.capability))
      }
    }
  }
</script>
