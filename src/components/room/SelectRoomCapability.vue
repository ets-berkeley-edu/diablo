<template>
  <div class="d-flex align-end">
    <label id="select-room-capability-label" for="select-room-capability" class="capability-label text-subtitle-1 mr-4">
      <span class="sr-only">Room </span>Capability:
    </label>
    <v-select
      id="select-room-capability"
      v-model="capability"
      :aria-describedby="undefined"
      :aria-label="undefined"
      autocomplete="off"
      hide-details
      item-props
      :items="capabilityOptions"
      :list-props="{ariaLabel: 'Room capability', ariaLive: 'off', id: 'room-capability-list'}"
      :menu-props="{attach: menuContainer, eager: true, id: 'room-capability-menu'}"
      no-data-text="Select..."
      return-object
      :title="undefined"
      :value="get(capability, 'title', undefined)"
      @update:menu="onToggleMenu"
      @update:model-value="updateCapability"
    />
    <div id="room-capability-menu-container" ref="menuContainer" />
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {each, get} from 'lodash'
import {putFocusNextTick} from '@/lib/utils'
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
  ariaLabel: 'None',
  id: 'room-capability-option-none',
  role: 'option',
  title: 'None',
  value: null,
}])
const menuContainer = ref()

onMounted(() => {
  capability.value = props.room.capability
  each(props.options, (text, value) => {
    capabilityOptions.value.push(
      {
        ariaLabel: text,
        id: `room-capability-option-${value}`,
        role: 'option',
        title: text,
        value: value
      }
    )
  })
})

const onToggleMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick('room-capability-option-none')
  }
}

const updateCapability = () => {
  updateRoomCapability(props.room.id, capability.value.value).then(() => {
    props.onUpdate(capability.value.value)
  })
}
</script>
