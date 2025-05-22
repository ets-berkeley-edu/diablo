<template>
  <div>
    <span class="sr-only">Meeting days: {{ oxfordJoin(namesOfDays) }}</span>
    <div :aria-hidden="true">
      <span v-for="(day, index) in namesOfDays" :key="index" :title="day">
        <span>{{ day.slice(0, 2).toUpperCase() }}</span>
        <span v-if="showComma(index)">, </span>
      </span>
    </div>
  </div>
</template>

<script setup>
import {defineProps} from 'vue'
import {oxfordJoin} from '@/lib/utils'

const props = defineProps({
  namesOfDays: {
    required: true,
    type: Array
  }
})

const showComma = index => props.namesOfDays.length > 1 && index < props.namesOfDays.length - 1
</script>
