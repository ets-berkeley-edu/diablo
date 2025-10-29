<template>
  <v-footer
    id="footer"
    app
    color="secondary"
  >
    <v-container fluid class="pa-0 pa-md-1">
      <v-row no-gutters>
        <v-col cols="12" sm="6">
          <ContactUsPrompt href-mailto-class="on-secondary" email-id-suffix="footer" />
        </v-col>
        <v-col class="d-flex justify-end" cols="12" sm="6">
          <span v-if="config.isVueAppDebugMode && get(screenReaderAlert, 'message', '').length">
            {{ screenReaderAlert.message }}
          </span>
          <span v-if="!config.isVueAppDebugMode || !get(screenReaderAlert, 'message', '').length">
            <v-icon :icon="mdiCopyright" size="small" />
            <span class="sr-only">Copyright</span> {{ new Date().getFullYear() }}
            The Regents of the University of California
          </span>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>

<script setup>
import {get} from 'lodash'
import {mdiCopyright} from '@mdi/js'
import {storeToRefs} from 'pinia'
import ContactUsPrompt from '@/components/util/ContactUsPrompt'
import {useContextStore} from '@/stores/context'

const {config, screenReaderAlert} = storeToRefs(useContextStore())

</script>
