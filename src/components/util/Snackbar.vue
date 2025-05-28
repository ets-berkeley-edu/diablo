<template>
  <div id="snackbar-container" aria-live="assertive" role="alert">
    <v-snackbar
      v-model="snackbarShow"
      attach="#snackbar-container"
      :color="snackbar.color"
      content-class="align-center"
      location="top"
      :timeout="snackbar.timeout"
    >
      <div class="d-flex align-center justify-space-between py-1">
        <div id="alert-text" class="px-4">
          <div class="text-h6">{{ snackbar.text }}</div>
          <ContactUsPrompt
            v-if="includeContactUsPrompt"
            class="mb-4"
            href-mailto-class="text-white"
          />
        </div>
        <div>
          <v-btn
            id="btn-close-alert"
            aria-label="Close alert"
            variant="text"
            @click="contextStore.snackbarClose"
          >
            Close
          </v-btn>
        </div>
      </div>
    </v-snackbar>
  </div>
</template>

<script setup>
import {watch} from 'vue'
import {storeToRefs} from 'pinia'
import ContactUsPrompt from '@/components/util/ContactUsPrompt'
import {putFocusNextTick} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

defineProps({
  includeContactUsPrompt: {
    required: false,
    type: Boolean,
  }
})

const contextStore = useContextStore()
const {snackbar, snackbarShow} = storeToRefs(contextStore)

watch(snackbarShow, isShowing => {
  if (isShowing) {
    putFocusNextTick('btn-close-alert')
  }
})
</script>
