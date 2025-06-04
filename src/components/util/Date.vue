<template>
  <component :is="tag">
    <span :aria-hidden="true">
      {{ DateTime.fromISO(date).toLocaleString(DateTime.DATE_MED) }}
    </span>
    <span class="sr-only">
      {{ DateTime.fromISO(date).toLocaleString(DateTime.DATE_FULL) }}
    </span>
  </component>
</template>

<script setup>
import {DateTime} from 'luxon'

defineProps({
  date: {
    required: true,
    type: String
  },
  tag: {
    default: 'span',
    required: false,
    type: String
  }
})
</script>
