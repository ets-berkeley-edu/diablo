<template>
  <div>
    {{ section }}
  </div>
</template>

<script>
  export default {
    name: 'SignUp',
    data: () => ({
      section: undefined
    }),
    created() {
      const termId = this.$_.get(this.$route, 'params.termId')
      const sectionId = this.$_.get(this.$route, 'params.sectionId')
      this.section = this.$_.find(this.$currentUser.teachingSections, s => s['sectionId'] === sectionId && s['termId'] === termId)
    }
  }
</script>

<style scoped>

</style>
