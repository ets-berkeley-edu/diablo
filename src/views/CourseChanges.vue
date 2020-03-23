<template>
  <div v-if="!loading">
    <div class="pl-3">
      <h2><v-icon class="pb-3" large>mdi-swap-horizontal</v-icon> Course Changes</h2>
    </div>
    <v-card>
      TODO
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'

  export default {
    name: 'CourseChanges',
    mixins: [Context],
    created() {
      this.$ready()
    }
  }
</script>
