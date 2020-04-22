<template>
  <v-app :id="$vuetify.theme.dark ? 'dark' : 'light'">
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
        class="title">{{ snackbar.text }}</span>
      <v-btn
        id="btn-close-alert"
        text
        @click="snackbarClose"
      >
        Close
      </v-btn>
    </v-snackbar>
    <router-view />
  </v-app>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'App',
    mixins: [Context]
  }
</script>

<style>
  @import './assets/styles/diablo-dark.css';
  @import './assets/styles/diablo-global.css';
  @import './assets/styles/diablo-light.css';
</style>
