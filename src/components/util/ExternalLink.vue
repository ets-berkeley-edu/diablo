<template>
  <a
    :id="linkId"
    :href="href"
    target="_blank"
  >
    <slot />
    <span class="sr-only">&nbsp;(opens in new tab)</span>
    <v-icon class="external-link-icon" :icon="mdiOpenInNew" :size="iconSize" />
  </a>
</template>

<script setup>
import {computed} from 'vue'
import {mdiOpenInNew} from '@mdi/js'

const props = defineProps({
  iconSize: {
    default: 14,
    required: false,
    type: Number
  },
  href: {
    required: true,
    type: String
  },
  linkId: {
    required: true,
    type: String
  },
})

const iconBottomMargin = computed(() => `${props.iconSize - 13}px`)
</script>

<style scoped>
.external-link-icon {
  margin: 0 4px 0 4px;
  margin-bottom: v-bind(iconBottomMargin);
}
</style>
