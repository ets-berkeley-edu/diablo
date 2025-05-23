<template>
  <v-switch
    :id="`job-${job.key}-enabled`"
    v-model="enabled"
    :aria-describedby="undefined"
    :aria-label="`Job ${job.name} is ${enabled ? 'enabled' : 'disabled'}`"
    color="success"
    hide-details
    @update:model-value="onChange(job, !enabled)"
  >
  </v-switch>
</template>

<script setup>
import {onMounted, ref} from 'vue'

const props = defineProps({
  job: {
    required: true,
    type: Object
  },
  onChange: {
    required: true,
    type: Function
  }
})

const enabled = ref()

onMounted(() => {
  enabled.value = !props.job.disabled
})
</script>
