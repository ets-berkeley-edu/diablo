<template>
  <v-app>
    <v-app-bar
      app
      color="primary"
      dark
    >
      <div v-if="$currentUser.isAdmin" class="d-flex align-center">
        <router-link
          id="home-header"
          class="header-text"
          to="/"
          tabindex="0">
          <span class="sr-only">Return to </span>Home
        </router-link>
      </div>
      <v-spacer></v-spacer>
      <v-menu v-if="$currentUser.isAuthenticated" class="mr-2" offset-y>
        <template v-slot:activator="{ on }">
          <v-btn
            color="primary"
            dark
            v-on="on"
          >
            {{ $currentUser.firstName }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item
            :href="`mailto:${$config.supportEmailAddress}`"
            target="_blank"
            aria-label="Send email to the Course Capture support team; this link opens a new tab.">
            <v-list-item-title>Feedback/Help</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logOut">
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
  import { getCasLogoutUrl } from '@/api/auth'

  export default {
    name: 'App',
    methods: {
      logOut() {
        getCasLogoutUrl().then(data => window.location.href = data.casLogoutUrl);
      }
    }
  }
</script>
