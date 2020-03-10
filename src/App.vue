<template>
  <v-app>
    <v-app-bar
      app
      color="primary"
      dark
    >
      <div v-if="$currentUser.isAuthenticated && $route.name !== 'home'">
        <v-btn
          color="primary"
          fab
          small
          dark
          @click="goHome">
          <v-icon>mdi-home</v-icon>
        </v-btn>
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
          <v-list-item @click="goAttic">
            <v-list-item-title>The Attic</v-list-item-title>
          </v-list-item>
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
    <v-footer class="white lighten-1" dark min-width="100%">
      <v-container fluid>
        <v-row class="mb-2" no-gutters>
          <v-col>
            <v-card
              color="white"
              class="black--text pa-2"
              outlined
              tile>
              <img alt="UC Berkeley logo" src="@/assets/uc-berkeley-logo.svg" />
            </v-card>
          </v-col>
          <v-col class="font-weight-light" offset-md="4">
            <v-card
              class="black--text pa-2 subtitle-2 text--disabled"
              color="white"
              outlined
              tile>
              <div class="text-no-wrap">
                Problem? Question? Email us at {{ $config.supportEmailAddress }}
              </div>
              <div>
                <v-icon small color="grey">mdi-copyright</v-icon> {{ new Date().getFullYear() }}
                The Regents of the University of California
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script>
  import router from '@/router'
  import { getCasLogoutUrl } from '@/api/auth'

  export default {
    name: 'App',
    methods: {
      goAttic: () => router.push({ path: '/attic' }),
      goHome: () => router.push({ path: '/' }),
      logOut: () =>getCasLogoutUrl().then(data => window.location.href = data.casLogoutUrl)
    }
  }
</script>

<style>
@import './assets/styles/diablo-global.css';
</style>
