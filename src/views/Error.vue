<template>
  <div class="pa-4">
    <v-banner class="pa-12">
      <template #prepend>
        <v-icon
          class="my-2"
          color="warning"
          :icon="mdiAlert"
          size="40"
        />
      </template>
      <div>
        <div class="pb-2">
          <h1 id="page-title" class="sr-only">Error</h1>
          <span
            v-if="!contextStore.loading"
            id="error-message"
            aria-live="polite"
            class="font-size-24"
            role="alert"
          >
            {{ message || 'Uh oh, there was a problem.' }}
          </span>
        </div>
        <div>
          <ContactUsPrompt class="font-size-18" />
        </div>
      </div>
    </v-banner>
  </div>
</template>

<script setup>
import {mdiAlert} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'
import {useContextStore} from '@/stores/context'
import ContactUsPrompt from '@/components/util/ContactUsPrompt'

const contextStore = useContextStore()
const message = ref()

onMounted(() => {
  message.value = useRoute().query.m
  contextStore.loadingComplete('Error')
})
</script>
