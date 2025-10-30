<template>
  <div class="align-start d-flex">
    <div>
      <v-icon class="mr-3" :color="color" :icon="icon" />
    </div>
    <div :class="`text-${color}`">
      <slot />{{ text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import {mdiAlert} from '@mdi/js'

defineProps({
  color: {
    default: 'error',
    required: false,
    type: String
  },
  icon: {
    default: mdiAlert,
    required: false,
    type: String
  },
  text: {
    default: undefined,
    required: false,
    type: String
  }
})
</script>
