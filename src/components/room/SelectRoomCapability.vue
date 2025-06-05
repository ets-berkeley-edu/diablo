<template>
  <div class="d-flex align-end">
    <label for="select-room-capability" class="capability-label text-subtitle-1 mr-4">Capability:</label>
    <v-select
      id="select-room-capability"
      v-model="capability"
      :aria-describedby="undefined"
      hide-details
      item-title="text"
      item-value="value"
      :items="capabilityOptions"
      :list-props="{ariaLabel: 'Room capability options', id: 'room-capability-list'}"
      :menu-props="{attach: menuContainer, eager: true, id: 'room-capability-menu'}"
      no-data-text="Select..."
      @update:model-value="updateCapability"
    />
    <div id="room-capability-menu-container" ref="menuContainer" />
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {each} from 'lodash'
import {alertScreenReader} from '@/lib/utils'
import {updateRoomCapability} from '@/api/room'

const props = defineProps({
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
    type: Object
  }
})

const capability = ref()
const capabilityOptions = ref([{
  'text': 'None',
  'value': null,
}])
const menuContainer = ref()

onMounted(() => {
  capability.value = props.room.capability
  each(props.options, (text, value) => {
    capabilityOptions.value.push({text, value})
  })
})

const updateCapability = () => {
  updateRoomCapability(props.room.id, capability.value).then(() => {
    props.onUpdate(capability.value)
    alertScreenReader(`${props.room.location} capability set to ${capability.value || 'none'}.`)
  })
}
</script>
