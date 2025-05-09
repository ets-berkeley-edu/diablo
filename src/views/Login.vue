<template>
  <v-app :id="$vuetify.theme.dark ? 'dark' : 'light'">
    <Snackbar include-contact-us-prompt />
    <v-container class="background-splash" fill-height fluid>
      <v-main>
        <v-card
          class="mx-auto opaque-card"
          elevation="24"
          max-width="400"
        >
          <v-banner class="accent--text px-8" bg-color="secondary">
            <div class="header-bar text-center w-100">
              <h1 id="page-title">Welcome to {{ contextStore.config.currentTermName }} Course Capture</h1>
            </div>
          </v-banner>
          <v-container fluid>
            <v-row dense>
              <v-col cols="12">
                <v-btn
                  id="log-in"
                  aria-label="Log in to Course Capture. (You will be sent to CalNet login page.)"
                  block
                  color="red"
                  dark
                  x-large
                  @click="logIn"
                >
                  Sign In
                  <v-icon class="pl-2">mdi-arrow-right-circle-outline</v-icon>
                </v-btn>
              </v-col>
              <v-col v-if="contextStore.config.devAuthEnabled">
                <div class="mb-8 ml-6 mr-6 mt-8">
                  <hr />
                </div>
                <v-card class="opaque-card pa-4" color="transparent" flat>
                  <v-form @submit.prevent="devAuth">
                    <v-text-field
                      id="dev-auth-uid"
                      v-model="devAuthUid"
                      bg-color="white"
                      outlined
                      placeholder="UID"
                      :rules="[v => !!v || 'Required']"
                    ></v-text-field>
                    <v-text-field
                      id="dev-auth-password"
                      v-model="devAuthPassword"
                      bg-color="white"
                      outlined
                      placeholder="Password"
                      :rules="[v => !!v || 'Required']"
                      type="password"
                    ></v-text-field>
                    <v-btn
                      id="btn-dev-auth-login"
                      block
                      :color="!devAuthUid || !devAuthPassword ? 'red lighten-2' : 'red'"
                      dark
                      large
                      @click="devAuth"
                    >
                      Dev
                      <v-icon dark>mdi-emoticon-devil-outline</v-icon>
                      Auth
                    </v-btn>
                  </v-form>
                </v-card>
              </v-col>
            </v-row>
          </v-container>
        </v-card>
      </v-main>
    </v-container>
  </v-app>
</template>

<script setup>
import {computed, onMounted, onUnmounted, ref} from 'vue'

import Snackbar from '@/components/util/Snackbar'
import {devAuthLogIn, getCasLoginURL} from '@/api/auth'
import {useContextStore} from '@/stores/context'
import router from '@/router'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils';
import {get, trim} from 'lodash'

const contextStore = useContextStore()

const devAuthUid = ref(undefined)
const devAuthPassword = ref(undefined)

onMounted(() => {
  putFocusNextTick('page-title')
  const error = get(router.currentRoute, 'query.error')
  if (error) {
    contextStore.snackbarReportError(error)
  } else {
    alertScreenReader('Welcome to Course Capture. Please log in.')
  }
})

const devAuth = () => {
  let uid = trim(devAuthUid.value)
  let password = trim(devAuthPassword.value)
  if (uid && password) {
    devAuthLogIn(uid, password).then(data => {
      if (data.isAuthenticated) {
        const redirect = get(router, 'currentRoute.query.redirect')
        router.push({path: redirect || '/home'}, this.$_.noop)
        alertScreenReader('Welcome to Course Capture')
      } else {
        const message = get(data, 'response.data.message') || get(data, 'message') || 'Authentication failed'
        contextStore.snackbarReportError(message)
      }
    },
    error => {
      contextStore.snackbarReportError(error)
    })
  } else if (uid) {
    contextStore.snackbarReportError('Password required')
    putFocusNextTick('dev-auth-password')
  } else {
    contextStore.snackbarReportError('Both UID and password are required')
    putFocusNextTick('dev-auth-uid')
  }
}

const logIn = () => {
  getCasLoginURL().then((data) => {
    window.location.href = data.data.casLoginUrl
  })
}
</script>

<style scoped>
  h1 {
    font-size: 18px;
  }
  .background-splash {
    background: url('@/assets/sather-gate.png') no-repeat center;
    -webkit-background-size: cover;
    -moz-background-size: cover;
    -o-background-size: cover;
    align-items: center;
    background-size: cover;
    display: flex;
    height: 100vh;
  }
  .header-bar {
    opacity: 1.0;
  }
  .opaque-card {
    background-color: rgba(255, 255, 255, 0.3);
  }
</style>
