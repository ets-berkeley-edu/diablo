<template>
  <v-app :id="$vuetify.theme.dark ? 'dark' : 'light'">
    <Snackbar />
    <v-container class="background-splash" fill-height fluid>
      <v-content>
        <v-card
          class="mx-auto opaque-card"
          elevation="24"
          max-width="400"
        >
          <v-system-bar class="accent--text pa-8" color="secondary">
            <div class="header-bar text-center w-100">
              <h1>Welcome to Course Capture</h1>
            </div>
          </v-system-bar>
          <v-container fluid>
            <v-row dense>
              <v-col cols="12">
                <v-card class="opaque-card" color="transparent" flat>
                  <v-card-actions>
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
                  </v-card-actions>
                </v-card>
              </v-col>
              <v-col v-if="$config.devAuthEnabled">
                <div class="mb-8 ml-6 mr-6 mt-8">
                  <hr />
                </div>
                <v-card class="opaque-card pa-4" color="transparent" flat>
                  <v-form @submit.prevent="devAuth">
                    <v-text-field
                      id="dev-auth-uid"
                      v-model="devAuthUid"
                      background-color="white"
                      outlined
                      placeholder="UID"
                      :rules="[v => !!v || 'Required']"
                    ></v-text-field>
                    <v-text-field
                      id="dev-auth-password"
                      v-model="devAuthPassword"
                      background-color="white"
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
      </v-content>
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
    font-size: 24px;
  }
  .background-splash {
    background: url('~@/assets/sather-gate.png') no-repeat center;
    -webkit-background-size: cover;
    -moz-background-size: cover;
    -o-background-size: cover;
    background-size: cover;
  }
  .header-bar {
    opacity: 1.0;
  }
  .opaque-card {
    background-color: rgba(255, 255, 255, 0.3);
  }
</style>
