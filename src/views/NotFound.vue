<template>
  <div v-if="!loading">
    <h1>Uh oh!</h1>
    <div>
      Page not found.
    </div>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'NotFound',
    mixins: [Context]
  }
</script>
