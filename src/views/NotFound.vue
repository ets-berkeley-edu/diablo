<template>
  <div v-if="!loading">
    <h2>Uh oh!</h2>
    <div>
      Page not found.
    </div>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'NotFound',
    mixins: [Context],
    created() {
      this.$ready()
    }
  }
</script>
