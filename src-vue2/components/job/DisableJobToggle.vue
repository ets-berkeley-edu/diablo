<template>
  <v-switch
    :id="`job-${job.key}-enabled`"
    v-model="enabled"
    :aria-label="`Job ${job.name} is ${enabled ? 'enabled' : 'disabled'}`"
    color="success"
    @change="onChange(job, !enabled)"
  >
  </v-switch>
</template>

<script>
export default {
  name: 'DisableJobToggle',
  props: {
    job: {
      required: true,
      type: Object
    },
    onChange: {
      required: true,
      type: Function
    }
  },
  data: () => ({
    enabled: undefined
  }),
  created() {
    this.enabled = !this.job.disabled
  }
}
</script>
