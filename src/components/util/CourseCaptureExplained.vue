<template>
  <div>
    The Course Capture program is the campus service for recording and publishing classroom activity. If you
    sign up using this form, recordings of every class session will be automatically recorded. (For details,
    please read
    <a
      id="link-to-course-capture-overview"
      :href="context.config.courseCaptureExplainedUrl"
      target="_blank"
    >
      Course Capture Services Explained <span class="sr-only">(opens in new tab)</span>
      <v-icon :icon="mdiOpenInNew" size="small" />
    </a>.
  </div>
</template>

<script setup>
import {mdiOpenInNew} from '@mdi/js'
import {useContextStore} from '@/stores/context'

const context = useContextStore()
</script>
