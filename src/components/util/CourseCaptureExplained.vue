<template>
  <div>
    The Course Capture program is the campus service for recording and publishing classroom activity. If you
    sign up using this form, recordings of every class session will be automatically recorded. (For details,
    please read
    <a
      id="link-to-course-capture-overview"
      aria-label="Open URL to Course Capture service overview in a new window"
      class="text-anchor"
      :href="config.courseCaptureExplainedUrl"
      target="_blank"
    >
      Course Capture Services Explained <v-icon>mdi-open-in-new</v-icon>
    </a>.
  </div>
</template>

<script>
import Context from '@/mixins/Context.vue';

export default {
  name: 'CourseCaptureExplained',
  mixins: [Context],
}
</script>
