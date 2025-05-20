<template>
  <span>
    <span v-for="(item, index) in items" :key="index">
      <slot :item="item"></slot>
      <span
        v-if="items.length > 1 && index === items.length - 2"
      >
        <span v-if="items.length > 2">,</span> and
      </span>
      <span
        v-if="items.length > 1 && index < items.length - 2"
      >, </span>
    </span>
  </span>
</template>

<script setup>
import {defineOptions, defineProps} from 'vue'

defineOptions({
  name: 'OxfordJoin'
})

defineProps({
  items: {
    type: Array,
    required: true
  }
})
</script>
