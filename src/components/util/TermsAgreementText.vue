<template>
  <div class="pt-1">
    <label id="permission-agreement" for="agree-to-terms-checkbox">
      I have read the Audio and Video Recording Permission Agreement and I agree to the terms stated within.
      <a
        id="link-to-course-capture-policies"
        :href="$config.courseCapturePoliciesUrl"
        target="_blank"
        aria-label="Open URL to Course Capture policies in a new window"
      >
        Audio and Video Recording Permission Agreement <v-icon>mdi-open-in-new</v-icon>
      </a>.
    </label>
  </div>
</template>

<script>
export default {
  name: 'CourseCaptureAgreement'
}
</script>
