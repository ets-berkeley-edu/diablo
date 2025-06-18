<template>
  <div>
    <v-switch
      :id="`toggle-opt-out-${switchId}`"
      v-model="optOut"
      :aria-describedby="undefined"
      :aria-label="ariaLabel"
      class="toggle-opt-out"
      color="primary"
      :disabled="disabled"
      flat
      hide-details
      inset
      :label="label ? `Opt out ${label}` : ''"
      @update:model-value="toggleOptOut"
    />
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {putFocusNextTick} from '@/lib/utils'
import {updateOptOut} from '@/api/course'

const props = defineProps({
  ariaLabel: {
    required: false,
    type: String,
    default: undefined
  },
  beforeToggle: {
    default: () => {},
    required: false,
    type: Function
  },
  disabled: {
    required: false,
    type: Boolean
  },
  initialValue: {
    required: true,
    type: Boolean
  },
  instructorUid: {
    required: true,
    type: String
  },
  label: {
    required: false,
    type: String,
    default: undefined
  },
  onToggle: {
    default: () => {},
    required: false,
    type: Function
  },
  sectionId: {
    required: true,
    type: String
  },
  termId: {
    required: true,
    type: String
  }
})

const optOut = ref(undefined)
const switchId = ref(undefined)

onMounted(() => {
  optOut.value = props.initialValue
  if (props.sectionId === 'all') {
    switchId.value = props.termId === 'all' ? 'all-terms' : 'current-term'
  } else {
    switchId.value = props.sectionId
  }
})

const toggleOptOut = () => {
  props.beforeToggle()
  updateOptOut(props.instructorUid, props.termId, props.sectionId, optOut.value).then(data => {
    props.onToggle(`Opted ${data.optedOut ? 'out' : 'in'} ${props.label}`)
    putFocusNextTick(`toggle-opt-out-${switchId.value}`)
  })
}
</script>

<style>
.toggle-opt-out label {
  font-size: 1.25rem;
  font-weight: 600;
  padding-inline: 12px !important;
}
</style>
