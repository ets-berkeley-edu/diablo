<template>
  <span>
    Problem? Question? Email us at
    <a
      id="diablo-support-mailto"
      aria-label="Open new window to send email"
      :class="hrefMailtoClass"
      :href="`mailto:${config.emailCourseCaptureSupport}`"
      target="_blank"
    >
      {{ config.emailCourseCaptureSupport }}
    </a>
  </span>
</template>

<script setup>
import {storeToRefs} from 'pinia'
import {useContextStore} from '@/stores/context'

const {config} = storeToRefs(useContextStore())

defineProps({
  hrefMailtoClass: {
    default: 'text-anchor',
    required: false,
    type: String
  }
})
</script>
