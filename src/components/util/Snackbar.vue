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
          <div v-if="includeToolDescription" class="py-2">
            This application is for instructors to adjust their Course Capture settings and does not host recordings.
            <ExternalLink
              class="text-white"
              href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0010426"
              link-id="link-find-recordings"
            >
              <span class="text-decoration-underline">Please see this article on where to find recordings.</span>
            </ExternalLink>
          </div>
          <ContactUsPrompt
            v-if="includeContactUsPrompt"
            class="mb-4"
            href-mailto-class="text-decoration-underline text-white"
            email-id-suffix="snackbar"
          />
        </div>
        <v-btn
          id="btn-close-alert"
          aria-label="Close alert"
          variant="text"
          @click="contextStore.snackbarClose"
        >
          Close
        </v-btn>
      </div>
    </v-snackbar>
  </div>
</template>

<script setup>
import {watch} from 'vue'
import {storeToRefs} from 'pinia'
import ContactUsPrompt from '@/components/util/ContactUsPrompt'
import ExternalLink from '@/components/util/ExternalLink'
import {putFocusNextTick} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

defineProps({
  includeContactUsPrompt: {
    required: false,
    type: Boolean,
  },
  includeToolDescription: {
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
