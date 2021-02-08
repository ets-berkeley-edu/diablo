<template>
  <v-banner class="pa-8">
    <v-icon
      slot="icon"
      color="warning"
      x-large
    >
      mdi-alert
    </v-icon>
    <div>
      <div class="pb-2">
        <h1 class="sr-only">Error</h1>
        <span id="error-message" aria-live="polite" role="alert">{{ message || 'Uh oh, there was a problem.' }}</span>
      </div>
      <div>
        Problem? Question?
        Email us at <a id="help-mailto" :href="`mailto:${$config.emailCourseCaptureSupport}`" target="_blank">{{ $config.emailCourseCaptureSupport }}</a>.
      </div>
    </div>
  </v-banner>
</template>

<script>
export default {
  name: 'Error',
  data: () => ({
    message: undefined
  }),
  mounted() {
    this.message = this.$route.query.m
    this.$ready('Error')
  }
}
</script>
