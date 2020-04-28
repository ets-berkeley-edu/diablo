<template>
  <v-footer app dark color="secondary">
    <v-container fluid class="pa-1">
      <v-row no-gutters justify="space-between">
        <v-col>
          Problem? Question? Email us at
          <a
            id="diablo-support-mailto"
            class="white--text"
            :href="`mailto:${$config.supportEmailAddress}`"
            target="_blank">
            {{ $config.supportEmailAddress }}
          </a>
        </v-col>
        <v-col>
          <div class="float-right">
            <v-icon small>mdi-copyright</v-icon> {{ new Date().getFullYear() }}
            The Regents of the University of California
          </div>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>

<script>
  export default {
    name: 'Footer'
  }
</script>
