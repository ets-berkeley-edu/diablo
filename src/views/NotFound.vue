<template>
  <div v-if="!loading">
    <h1>Uh oh!</h1>
    <div id="page-not-found" aria-live="polite" role="alert">
      Page not found.
    </div>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'NotFound',
    mixins: [Context],
    mounted() {
      this.$ready('Page not found')
    }
  }
</script>
