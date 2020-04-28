<template>
  <v-app :id="$vuetify.theme.dark ? 'dark' : 'light'">
    <Snackbar />
    <v-container fluid fill-height :class="{'background-splash': $route.meta.splash}">
      <v-app-bar
        app
        color="header-background"
        dark
      >
        <h1>Welcome to Course Capture</h1>
        <v-spacer />
        <v-btn
          id="log-in"
          light
          rounded
          @click="logIn">
          <span>Sign In</span>
          <v-icon>mdi-login</v-icon>
        </v-btn>
      </v-app-bar>
      <v-footer v-if="$config.devAuthEnabled" color="transparent" fixed>
        <v-form @submit.prevent="devAuth">
          <div class="d-flex">
            <div class="pr-3">
              <v-text-field
                id="dev-auth-uid"
                v-model="devAuthUid"
                background-color="#e8f0fe"
                class="input-dev-auth"
                dark
                label="UID"
                name="devAuth"
                prepend-icon="person"
                :rules="[v => !!v || 'Required']"
                size="16"
                solo
                type="text"></v-text-field>
            </div>
            <div class="pr-4">
              <v-text-field
                id="dev-auth-password"
                v-model="devAuthPassword"
                background-color="#e8f0fe"
                dark
                label="Password"
                name="password"
                prepend-icon="lock"
                :rules="[v => !!v || 'Required']"
                size="16"
                solo
                type="password"></v-text-field>
            </div>
            <div class="btn-dev-auth">
              <v-btn
                id="btn-dev-auth-login"
                aria-label="Log in to Course Capture. (You will be sent to CalNet login page.)"
                fab
                light
                small
                @click="devAuth">
                <v-icon dark>mdi-emoticon-devil-outline</v-icon>
              </v-btn>
            </div>
          </div>
        </v-form>
      </v-footer>
    </v-container>
  </v-app>
</template>

<script>
  import Snackbar from '@/components/util/Snackbar'
  import Utils from '@/mixins/Utils'
  import { devAuthLogIn, getCasLoginURL } from '@/api/auth'
  import Context from '@/mixins/Context'

  export default {
    name: 'Login',
    components: {Snackbar},
    mixins: [Context, Utils],
    data: () => ({
      devAuthUid: undefined,
      devAuthPassword: undefined
    }),
    methods: {
      devAuth() {
        let uid = this.$_.trim(this.devAuthUid)
        let password = this.$_.trim(this.devAuthPassword)
        if (uid && password) {
          devAuthLogIn(uid, password).then(data => {
              if (data.isAuthenticated) {
                const redirect = this.$_.get(this.$router, 'currentRoute.query.redirect')
                this.$router.push({ path: redirect || '/home' }, this.$_.noop)
              } else if (data.message) {
                this.reportError(data.message)
              } else {
                this.reportError('Sorry, authentication failed.')
              }
            },
            error => {
              this.reportError(error)
            }
          )
        } else if (uid) {
          this.reportError('Password required')
          this.putFocusNextTick('dev-auth-password')
        } else {
          this.reportError('Both UID and password are required')
          this.putFocusNextTick('dev-auth-uid')
        }
      },
      logIn() {
        getCasLoginURL().then(data => window.location.href = data.casLoginUrl)
      },
      reportError(msg) {
        this.snackbarReportError(msg)
      }
    }
  }
</script>

<style scoped>
  h1 {
    font-size: 3vw;
  }
  .background-splash {
    background: url('~@/assets/sather-gate.png') no-repeat center center fixed;
    -webkit-background-size: cover;
    -moz-background-size: cover;
    -o-background-size: cover;
    background-size: cover;
  }
  .btn-dev-auth {
    padding-top: 4px;
  }
</style>
