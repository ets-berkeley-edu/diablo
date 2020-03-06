<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <v-card class="elevation-12">
          <v-toolbar dark color="primary">
            <v-toolbar-title>Dev Auth</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="logIn">
              <v-text-field
                id="dev-auth-uid"
                v-model="devAuthUid"
                label="UID"
                name="login"
                prepend-icon="person"
                :rules="[v => !!v || 'Required']"
                type="text"></v-text-field>
              <v-text-field
                id="dev-auth-password"
                v-model="devAuthPassword"
                label="Password"
                name="password"
                prepend-icon="lock"
                :rules="[v => !!v || 'Required']"
                type="password"></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="logIn">Login</v-btn>
          </v-card-actions>
        </v-card>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
  import Utils from '@/mixins/Utils'
  import { devAuthLogIn } from '@/api/auth'

  export default {
    name: 'Login',
    mixins: [Utils],
    data: () => ({
      devAuthUid: undefined,
      devAuthPassword: undefined
    }),
    methods: {
      logIn() {
        let uid = this.$_.trim(this.devAuthUid)
        let password = this.$_.trim(this.devAuthPassword)
        if (uid && password) {
          devAuthLogIn(uid, password).then(user => {
            if (user.isAuthenticated) {
              const redirect = this.$_.get(this.$router, 'currentRoute.query.redirect')
              this.$router.push({ path: redirect || '/home' }, this.$_.noop)
            } else {
              this.reportError('Sorry, you are not authorized to use Diablo.')
            }
          })
        } else if (uid) {
          this.reportError('Password required')
          this.putFocusNextTick('dev-auth-password')
        } else {
          this.reportError('Both UID and password are required')
          this.putFocusNextTick('dev-auth-uid')
        }
      },
      reportError(msg) {
        console.log(msg)
      }
    }
  }
</script>
