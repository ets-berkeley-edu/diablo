<template>
  <v-switch
    :id="`toggle-opt-out-${course.sectionId}`"
    v-model="optOut"
    dense
    @change="toggleOptOut"
  ></v-switch>
</template>

<script>
import Context from '@/mixins/Context'
import {updateOptOut} from '@/api/course'

export default {
  name: 'ToggleOptOut',
  mixins: [Context],
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
        this.alertScreenReader(`${this.course.label} has opted ${data.hasOptedOut ? 'out' : 'in'}`)
        this.onToggle(this.course)
      })
    }
  }
}
</script>
