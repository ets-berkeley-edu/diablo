<template>
  <v-switch
    :id="`toggle-opt-in-${switchId}`"
    v-model="hasOptedIn"
    :aria-describedby="undefined"
    :aria-label="ariaLabel"
    class="toggle-opt-in"
    color="primary"
    density="compact"
    :disabled="disabled"
    flat
    hide-details
    inset
    @update:model-value="toggleOptIn"
  >
    <template #label>
      <slot />{{ label }}
    </template>
  </v-switch>
</template>

<script lang="ts" setup>
import {onMounted, ref} from 'vue'

const props = defineProps({
  ariaLabel: {
    required: false,
    type: String,
    default: undefined
  },
  disabled: {
    required: false,
    type: Boolean
  },
  label: {
    default: undefined,
    required: false,
    type: String
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

const hasOptedIn = defineModel({required: true, type: Boolean})
const switchId = ref<string | undefined>()

onMounted(() => {
  if (props.sectionId === 'all') {
    switchId.value = props.termId === 'all' ? 'all-terms' : 'current-term'
  } else {
    switchId.value = props.sectionId
  }
})

const toggleOptIn = () => {
  // props.beforeToggle()
  // const promises: Promise<void>[] = []
  // props.instructorUids.forEach((uid: string) => {
  //   const promise = new Promise<void>(resolve => {
  //     updateOptIn(uid, props.termId, props.sectionId, optIn.value).then(() => resolve())
  //   })
  //   promises.push(promise)
  // })
  // Promise.all(promises).then(() => {
  //   getCourse(props.termId, props.sectionId).then(data => {
  //     props.onToggle(data)
  //     putFocusNextTick(`toggle-opt-in-${switchId.value}`)
  //     alertScreenReader(`Opted ${optIn.value ? 'in' : 'out'} ${props.label || ''}`)
  //   })
  // })
}
</script>

<style>
.toggle-opt-in label {
  font-size: 1.25rem;
  font-weight: 500;
  padding-inline: 12px !important;
}
</style>
