<template>
  <div>
    <h1>The Attic</h1>
    {{ $route.name }}
    <div class="mr-3">
      <v-switch
        v-model="$vuetify.theme.dark"
        hide-details
        inset
        :label="$vuetify.theme.dark ? 'Dark' : 'Light'"></v-switch>
    </div>
    <v-container v-if="$vuetify.theme.dark" fluid fill-height>
      <v-layout align-center justify-center>
        <v-img src="@/assets/attic.png" />
      </v-layout>
    </v-container>
  </div>
</template>

<script>
  export default {
    name: 'Attic'
  }
</script>

<style scoped>

</style>
