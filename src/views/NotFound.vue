<template>
  <v-card
    v-if="!loading"
    class="elevation-1"
    outlined
  >
    <v-card-title>
      <PageTitle icon="mdi-sign-caution" text="Uh oh!" />
    </v-card-title>
    <v-card-text class="pl-8">
      <div
        id="page-not-found"
        aria-live="polite"
        class="body-1 pb-5"
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

<script>
import ContactUsPrompt from '@/components/util/ContactUsPrompt'
import Context from '@/mixins/Context'
import PageTitle from '@/components/util/PageTitle'

export default {
  name: 'NotFound',
  mixins: [Context],
  components: {ContactUsPrompt, PageTitle},
  mounted() {
    this.$ready('Page not found')
  }
}
</script>
