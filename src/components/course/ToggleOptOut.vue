<template>
  <v-switch v-model="optOut" dense @change="toggleOptOut()"></v-switch>
</template>

<script>
  import {updateOptOut} from '@/api/course'

  export default {
    name: 'ToggleOptOut',
    props: {
      course: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      optOut: undefined
    }),
    created() {
      this.optOut = this.course.hasOptedOut
    },
    methods: {
      toggleOptOut() {
        updateOptOut(this.course.termId, this.course.sectionId, this.optOut).then(data => {
          this.course.hasOptedOut = data.hasOptedOut
        })
      }
    }
  }
</script>
