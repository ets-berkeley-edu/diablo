<template>
  <v-banner class="pa-8">
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
        <h1 class="sr-only">Error</h1>
        <span
          v-if="!contextStore.loading"
          id="error-message"
          aria-live="polite"
          role="alert"
        >
          {{ message || 'Uh oh, there was a problem.' }}
        </span>
      </div>
      <div>
        <ContactUsPrompt />
      </div>
    </div>
  </v-banner>
</template>

<script setup>
import {mdiAlert} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {useContextStore} from '@/stores/context'
import {useRoute} from 'vue-router'
import ContactUsPrompt from '@/components/util/ContactUsPrompt'

const contextStore = useContextStore()
const message = ref()

onMounted(() => {
  message.value = useRoute().query.m
  contextStore.loadingComplete('Error')
})
</script>
