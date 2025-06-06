<template>
  <v-app theme="light">
    <Snackbar include-contact-us-prompt />
    <v-main>
      <v-container class="background-splash" fill-height fluid>
        <v-card
          class="mx-auto opaque-card"
          elevation="24"
          width="450"
        >
          <v-banner class="px-8" bg-color="secondary">
            <div class="header-bar text-center w-100">
              <h1 id="page-title" class="text-no-wrap">Welcome to {{ contextStore.config.currentTermName }} Course Capture</h1>
            </div>
          </v-banner>
          <v-container class="pa-6" fluid>
            <v-row class="px-4 py-2">
              <v-btn
                id="log-in"
                aria-label="Log in to Course Capture. (You will be sent to CalNet login page.)"
                block
                color="accent"
                size="x-large"
                @click="logIn"
              >
                Sign In
                <v-icon class="pl-2" :icon="mdiArrowRightCircleOutline" size="x-large" />
              </v-btn>
            </v-row>
            <v-row v-if="contextStore.config.devAuthEnabled">
              <hr class="mx-6 my-8 w-100" role="presentation">
            </v-row>
            <v-row>
              <v-card class="opaque-card pa-4 w-100" color="transparent" flat>
                <v-form @submit.prevent="devAuth">
                  <v-text-field
                    id="dev-auth-uid"
                    v-model="devAuthUid"
                    :aria-describedby="undefined"
                    aria-label="U I D"
                    bg-color="white"
                    class="mb-2"
                    hide-details
                    placeholder="UID"
                    :rules="[v => !!v || 'Required']"
                    variant="outlined"
                  />
                  <label class="sr-only" for="dev-auth-password">Password</label>
                  <v-text-field
                    id="dev-auth-password"
                    v-model="devAuthPassword"
                    :aria-describedby="undefined"
                    bg-color="white"
                    class="mb-2"
                    hide-details
                    placeholder="Password"
                    :rules="[v => !!v || 'Required']"
                    type="password"
                    variant="outlined"
                  />
                  <v-btn
                    id="btn-dev-auth-login"
                    block
                    color="accent"
                    :disabled="!devAuthUid || !devAuthPassword"
                    size="large"
                    @click="devAuth"
                  >
                    Dev
                    <v-icon class="mx-1" :icon="mdiEmoticonDevilOutline" size="large" />
                    Auth
                  </v-btn>
                </v-form>
              </v-card>
            </v-row>
          </v-container>
        </v-card>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {get, trim} from 'lodash'
import {mdiArrowRightCircleOutline, mdiEmoticonDevilOutline} from '@mdi/js'
import router from '@/router'
import Snackbar from '@/components/util/Snackbar'
import {devAuthLogIn, getCasLoginURL} from '@/api/auth'
import {useContextStore} from '@/stores/context'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'

const contextStore = useContextStore()

const devAuthUid = ref(undefined)
const devAuthPassword = ref(undefined)

onMounted(() => {
  contextStore.loadingComplete()
  putFocusNextTick('log-in')
  const error = get(router.currentRoute, 'query.error')
  if (error) {
    contextStore.snackbarReportError(error)
  } else {
    alertScreenReader('Welcome to Course Capture. Please log in.')
  }
})

const devAuth = () => {
  const uid = trim(devAuthUid.value)
  const password = trim(devAuthPassword.value)
  if (uid && password) {
    devAuthLogIn(uid, password).then(
      data => {
        if (data.isAuthenticated) {
          const redirect = get(router, 'currentRoute.query.redirect')
          router.push({path: redirect || '/home'})
          alertScreenReader('Welcome to Course Capture')
        } else {
          const message = get(data, 'response.data.message') || get(data, 'message') || 'Authentication failed'
          contextStore.snackbarReportError(message)
        }
      },
      error => {
        contextStore.snackbarReportError(error)
      }
    )
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
    window.location.href = data.casLoginUrl
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
