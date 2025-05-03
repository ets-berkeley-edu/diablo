<template>
  <v-snackbar
    v-model="snackbarShow"
    :color="snackbar.color"
    :timeout="snackbar.timeout"
    content-class="align-center"
    :top="true"
  >
    <div class="d-flex align-center justify-space-between">
      <div
        id="alert-text"
        aria-live="polite"
        class="ml-4 mr-4 title"
        role="alert"
      >
        {{ snackbar.text }}
        <ContactUsPrompt
          v-if="includeContactUsPrompt"
          href-mailto-class="white--text"
        />
      </div>
      <div>
        <v-btn
          id="btn-close-alert"
          aria-label="Close this dialog box."
          text
          @click="snackbarClose"
        >
          Close
        </v-btn>
      </div>
    </div>
  </v-snackbar>
</template>

<script>
import ContactUsPrompt from '@/components/util/ContactUsPrompt'
import Context from '@/mixins/Context'

export default {
  name: 'Snackbar',
  mixins: [Context],
  components: {ContactUsPrompt},
  props: {
    includeContactUsPrompt: {
      required: false,
      type: Boolean,
    }
  }
}
</script>
