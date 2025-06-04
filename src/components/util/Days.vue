<template>
  <div>
    <span class="sr-only">{{ oxfordJoin(namesOfDays) }}</span>
    <div :aria-hidden="true">
      <span v-for="(day, index) in namesOfDays" :key="index">
        <span>{{ day.slice(0, 2).toUpperCase() }}</span>
        <span v-if="showComma(index)">, </span>
      </span>
    </div>
  </div>
</template>

<script setup>
import {oxfordJoin} from '@/lib/utils'

const props = defineProps({
  namesOfDays: {
    required: true,
    type: Array
  }
})

const showComma = index => props.namesOfDays.length > 1 && index < props.namesOfDays.length - 1
</script>
