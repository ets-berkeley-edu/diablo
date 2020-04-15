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
    <v-app-bar
      v-if="!$route.meta.printable"
      app
      color="header-background"
      dark
    >
      <div>
        <h1>Course Capture</h1>
      </div>
      <v-spacer></v-spacer>
      <v-menu v-if="$currentUser.isAuthenticated" class="mr-2" offset-y>
        <template v-slot:activator="{ on }">
          <v-btn
            id="btn-main-menu"
            color="primary"
            dark
            v-on="on"
          >
            {{ $currentUser.firstName }}
          </v-btn>
        </template>
        <v-list class="pr-2">
          <v-list-item
            id="menu-item-feedback-and-help"
            :href="`mailto:${$config.supportEmailAddress}`"
            target="_blank"
            aria-label="Send email to the Course Capture support team; this link opens a new tab.">
            <v-list-item-title>Feedback/Help</v-list-item-title>
          </v-list-item>
          <v-list-item v-if="$currentUser.isAdmin" id="menu-item-email-templates" @click="goToPath('/email/templates')">
            <v-list-item-title>Email Templates</v-list-item-title>
          </v-list-item>
          <v-list-item v-if="$currentUser.isAdmin" id="menu-item-jobs" @click="goToPath('/jobs')">
            <v-list-item-title>Jobs</v-list-item-title>
          </v-list-item>
          <v-list-item id="menu-item-log-out" @click="logOut">
            <v-list-item-title>Log Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-content>
      <router-view />
    </v-content>
  </v-app>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import { getCasLogoutUrl } from '@/api/auth'

  export default {
    name: 'App',
    mixins: [Context, Utils],
    methods: {
      logOut: () => getCasLogoutUrl().then(data => window.location.href = data.casLogoutUrl)
    }
  }
</script>

<style>
  @import './assets/styles/diablo-dark.css';
  @import './assets/styles/diablo-global.css';
  @import './assets/styles/diablo-light.css';
</style>
