<template>
  <v-banner single-line class="pa-12">
    <v-icon
      slot="icon"
      color="warning"
      x-large
    >
      mdi-alert
    </v-icon>
    {{ message || 'Uh oh, there was a problem.' }}
    <template v-slot:actions>
      Problem? Question? Email us at
      <a id="help-mailto" :href="`mailto:${$config.supportEmailAddress}`" target="_blank">{{ $config.supportEmailAddress }}</a>
    </template>
  </v-banner>
</template>

<script>
  export default {
    name: 'Error',
    data: () => ({
      message: undefined
    }),
    mounted() {
      this.message = this.$route.query.m
      this.$ready()
    }
  }
</script>
