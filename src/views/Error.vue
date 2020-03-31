<template>
  <v-banner class="pa-8">
    <v-icon
      slot="icon"
      color="warning"
      x-large
    >
      mdi-alert
    </v-icon>
    <div>
      <div class="pb-2">
        {{ message || 'Uh oh, there was a problem.' }}
      </div>
      <div>
        Problem? Question?
        Email us at <a id="help-mailto" :href="`mailto:${$config.supportEmailAddress}`" target="_blank">{{ $config.supportEmailAddress }}</a>.
      </div>
    </div>
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
