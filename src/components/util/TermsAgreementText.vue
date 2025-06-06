<template>
  <div class="pt-1">
    <label id="permission-agreement" for="agree-to-terms-checkbox">
      I have read the Audio and Video Recording Permission Agreement and I agree to the terms stated within.
      <a
        id="link-to-course-capture-policies"
        :href="$config.courseCapturePoliciesUrl"
        target="_blank"
      >
        Audio and Video Recording Permission Agreement <span class="sr-only">(opens in new tab)</span>
        <v-icon :icon="mdiOpenInNew" />
      </a>.
    </label>
  </div>
</template>

<script setup>
import {mdiOpenInNew} from '@mdi/js'
</script>
