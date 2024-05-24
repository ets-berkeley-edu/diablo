<template>
  <v-switch
    :id="`toggle-opt-out-${sectionId}`"
    v-model="optOut"
    dense
    :disabled="disabled"
    :label="label"
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
    sectionId: {
      required: true,
      type: String
    },
    termId: {
      required: true,
      type: String
    },
    instructorUid: {
      required: true,
      type: String
    },
    initialValue: {
      required: true,
      type: Boolean
    },
    disabled: {
      required: false,
      type: Boolean
    },
    label: {
      required: false,
      type: String,
      default: undefined
    },
    beforeToggle: {
      default: () => {},
      required: false,
      type: Function
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
    this.optOut = this.initialValue
  },
  methods: {
    toggleOptOut() {
      this.beforeToggle()
      updateOptOut(this.instructorUid, this.termId, this.sectionId, this.optOut).then(data => {
        this.alertScreenReader(`Opted ${data.hasOptedOut ? 'out' : 'in'}`)
        this.onToggle()
      })
    }
  }
}
</script>
