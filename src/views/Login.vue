<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-card
        class="elevation-12 mx-auto"
        max-width="434"
        tile
      >
        <v-img
          alt=""
          role="button"
          height="100%"
          src="@/assets/iraqi-sunset-from-exorcist-movie.png"
          @click="logIn"
        >
          <div>
            <div class="d-flex ma-10">
              <div class="pr-5">
                <h2 class="display-4 fill-height white--text">Sign In</h2>
              </div>
              <div class="align-self-end mb-3">
                <v-icon color="white" large>mdi-open-in-new</v-icon>
              </div>
            </div>
            <div class="ml-5 mt-12 pt-5 title white--text">UC Berkeley's Course Capture service</div>
          </div>
        </v-img>
        <div v-if="$config.devAuthEnabled" class="pa-3">
          <v-form @submit.prevent="devAuth">
            <div class="mb-1 ml-2 mt-1">
              <h3 class="pb-1 text--disabled">Dev Auth</h3>
            </div>
            <div class="d-flex flex-wrap">
              <div class="pr-2">
                <v-text-field
                  id="dev-auth-uid"
                  v-model="devAuthUid"
                  label="UID"
                  name="devAuth"
                  prepend-icon="person"
                  :rules="[v => !!v || 'Required']"
                  size="12"
                  type="text"></v-text-field>
              </div>
              <div class="pr-2">
                <v-text-field
                  id="dev-auth-password"
                  v-model="devAuthPassword"
                  label="Password"
                  name="password"
                  prepend-icon="lock"
                  :rules="[v => !!v || 'Required']"
                  size="16"
                  type="password"></v-text-field>
              </div>
              <div class="align-self-center pb-2">
                <v-btn id="btn-dev-auth-login" color="primary" @click="devAuth">Login</v-btn>
              </div>
            </div>
          </v-form>
        </div>
      </v-card>
    </v-layout>
  </v-container>
</template>

<script>
  import Utils from '@/mixins/Utils'
  import { devAuthLogIn, getCasLoginURL } from '@/api/auth'
  import Context from '@/mixins/Context'

  export default {
    name: 'Login',
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
                this.reportError('Sorry, you are not authorized to use Diablo.')
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
