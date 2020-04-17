<template>
  <v-switch
    :id="`toggle-opt-out-${course.sectionId}`"
    v-model="optOut"
    dense
    @change="toggleOptOut()"
  ></v-switch>
</template>

<script>
  import {updateOptOut} from '@/api/course'

  export default {
    name: 'ToggleOptOut',
    props: {
      course: {
        required: true,
        type: Object
      },
      onToggle: {
        default: () => {},
        required: false,
        type: Function
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
          this.onToggle(this.course)
        })
      }
    }
  }
</script>
