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
  >
    <span :id="`room-capability-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item.text }}</span>
  </v-select>
</template>

<script>
  import Context from '@/mixins/Context'
  import {updateRoomCapability} from '@/api/room'

  export default {
    name: 'SelectRoomCapability',
    mixins: [Context],
    props: {
      isAuditorium: {
        required: true,
        type: Boolean
      },
      onUpdate: {
        required: true,
        type: Function
      },
      options: {
        required: true,
        type: Object
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
        updateRoomCapability(this.room.id, this.capability).then(() => {
          this.onUpdate(this.capability)
          this.alertScreenReader(`${this.room.location} capability set to ${this.capability || 'none'}.`)
        })
      }
    }
  }
</script>
