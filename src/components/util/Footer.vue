<template>
  <v-footer
    id="footer"
    app
    dark
    color="secondary"
  >
    <v-container fluid class="pa-1">
      <v-row no-gutters justify="space-between">
        <v-col>
          Problem? Question? Email us at
          <a
            id="diablo-support-mailto"
            class="white--text"
            :href="`mailto:${$config.emailCourseCaptureSupport}`"
            target="_blank"
          >
            {{ $config.emailCourseCaptureSupport }}
          </a>
        </v-col>
        <v-col>
          <div class="float-right">
            <span v-if="$config.isVueAppDebugMode && screenReaderAlert">
              {{ screenReaderAlert }}
            </span>
            <span v-if="!$config.isVueAppDebugMode || !screenReaderAlert">
              <v-icon small>mdi-copyright</v-icon> {{ new Date().getFullYear() }}
              The Regents of the University of California
            </span>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'Footer',
    mixins: [Context]
  }
</script>
