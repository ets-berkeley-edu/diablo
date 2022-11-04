<template>
  <span>
    Problem? Question? Email us at
    <a
      id="diablo-support-mailto"
      aria-label="Open new window to send email"
      :class="hrefMailtoClass"
      :href="`mailto:${$config.emailCourseCaptureSupport}`"
      target="_blank"
    >
      {{ $config.emailCourseCaptureSupport }}
    </a>
  </span>
</template>

<script>
export default {
  name: 'ContactUsPrompt',
  props: {
    hrefMailtoClass: {
      default: undefined,
      required: false,
      type: String
    }
  }
}
</script>
