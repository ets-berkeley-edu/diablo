<template>
  <v-select
    :id="`select-room-capability-${room.id}`"
    v-model="capability"
    density="comfortable"
    item-title="text"
    item-value="value"
    :items="capabilityOptions"
    no-data-text="Select..."
    variant="underlined"
    @update:model-value="updateCapability"
  />
</template>

<script setup>
import {defineProps, onMounted, ref} from 'vue'
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
