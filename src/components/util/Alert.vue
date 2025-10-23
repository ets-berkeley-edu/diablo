<template>
  <div class="align-start d-flex">
    <div>
      <v-icon class="mr-3" color="error" :icon="mdiAlert" />
    </div>
    <div :class="textClass">
      <slot />{{ text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import {mdiAlert} from '@mdi/js'

defineProps({
  textClass: {
    default: 'text-error',
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
