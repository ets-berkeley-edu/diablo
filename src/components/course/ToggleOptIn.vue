<template>
  <v-switch
    :id="`toggle-opt-in-${switchId}`"
    v-model="optIn"
    :aria-describedby="undefined"
    :aria-label="ariaLabel"
    class="toggle-opt-in"
    color="primary"
    :disabled="disabled"
    flat
    hide-details
    inset
    :label="label ? `Opt in ${label}` : ''"
    @update:model-value="toggleOptIn"
  />
</template>

<script lang="ts" setup>
import type {PropType} from 'vue'
import {onMounted, ref} from 'vue'
import {putFocusNextTick} from '@/lib/utils'
import {updateOptIn} from '@/api/course'

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
    required: false,
    type: Boolean
  },
  instructorUids: {
    required: true,
    type: Array as PropType<string[]>
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

const optIn = ref(props.initialValue)
const switchId = ref<string | undefined>()

onMounted(() => {
  if (props.sectionId === 'all') {
    switchId.value = props.termId === 'all' ? 'all-terms' : 'current-term'
  } else {
    switchId.value = props.sectionId
  }
})

const toggleOptIn = () => {
  props.beforeToggle()
  props.instructorUids.forEach((uid: string) => {
    updateOptIn(uid, props.termId, props.sectionId, optIn.value).then(data => {
      props.onToggle(`Opted ${data.optedIn ? 'in' : 'out'} ${props.label}`)
      putFocusNextTick(`toggle-opt-in-${switchId.value}`)
    })
  })

}
</script>

<style>
.toggle-opt-in label {
  font-size: 1.25rem;
  font-weight: 500;
  padding-inline: 12px !important;
}
</style>
