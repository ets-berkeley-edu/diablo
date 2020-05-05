<template>
  <v-snackbar
    v-model="snackbarShow"
    :color="snackbar.color"
    :timeout="snackbar.timeout"
    :top="true"
  >
    <span
      id="alert-text"
      aria-live="polite"
      role="alert"
      class="title"
    >{{ snackbar.text }}</span>
    <v-btn
      id="btn-close-alert"
      aria-label="Close this dialog box."
      text
      @click="snackbarClose"
    >
      Close
    </v-btn>
  </v-snackbar>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'Snackbar',
    mixins: [Context]
  }
</script>
