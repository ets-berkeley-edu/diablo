<template>
  <v-card
    class="elevation-1"
    outlined
  >
    <v-card-title>
      <PageTitle :icon="mdiSignCaution" text="Uh oh!" />
    </v-card-title>
    <v-card-text class="pl-8">
      <div
        id="page-not-found"
        aria-live="polite"
        class="text-body-1 pb-5"
        role="alert"
      >
        Page not found.
      </div>
      <div>
        <ContactUsPrompt />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import {mdiSignCaution} from '@mdi/js'
import {onMounted} from 'vue'
import ContactUsPrompt from '@/components/util/ContactUsPrompt'
import PageTitle from '@/components/util/PageTitle'
import {useContextStore} from '@/stores/context'

onMounted(() => {
  useContextStore().loadingComplete('Page not found')
})
</script>
