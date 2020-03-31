<template>
  <v-footer color="transparent" fixed>
    <v-container fluid>
      <v-row no-gutters>
        <v-spacer />
        <v-col class="font-weight-light" offset-md="4">
          <div class="text-no-wrap">
            Problem? Question? Email us at
            <a
              id="diablo-support-mailto"
              :href="`mailto:${$config.supportEmailAddress}`"
              target="_blank">
              {{ $config.supportEmailAddress }}
            </a>
          </div>
          <div>
            <v-icon small color="grey">mdi-copyright</v-icon> {{ new Date().getFullYear() }}
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
