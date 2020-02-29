<template>
  <v-app>
    <v-app-bar
      app
      color="primary"
      dark
    >
      <div v-if="$currentUser.isAdmin" class="d-flex align-center">
        Home
      </div>
      <v-spacer></v-spacer>
      <span v-if="$currentUser.isAuthenticated" class="mr-2">
        {{ $currentUser.name }}
      </span>
    </v-app-bar>

    <v-content>
      <router-view />
    </v-content>
  </v-app>
</template>

<script>
  export default {
    name: 'App'
  }
</script>
