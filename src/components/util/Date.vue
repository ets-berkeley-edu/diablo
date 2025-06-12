<template>
  <component :is="tag">
    <span :aria-hidden="true">
      {{ DateTime.fromISO(date).toLocaleString(format) }}
    </span>
    <span class="sr-only">
      {{ DateTime.fromISO(date).toLocaleString(accessibleFormat) }}
    </span>
  </component>
</template>

<script setup>
import {computed} from 'vue'
import {DateTime} from 'luxon'
import {has} from 'lodash'

const props = defineProps({
  date: {
    required: true,
    type: String
  },
  format: {
    default: DateTime.DATE_MED,
    require: false,
    type: Object
  },
  tag: {
    default: 'span',
    required: false,
    type: String
  }
})

const accessibleFormat = computed(() => {
  const format = {
    ...props.format,
    month: 'long'
  }
  if (has(props.format, 'weekday')) {
    format['weekday'] = 'long'
  }
  return format
})
</script>
