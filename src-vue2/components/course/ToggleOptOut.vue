<template>
  <div>
    <v-switch
      :id="`toggle-opt-out-${switchId}`"
      v-model="optOut"
      :aria-label="ariaLabel"
      dense
      :disabled="disabled"
      inset
      :label="label ? `Opt out ${label}` : ''"
      @blur="() => ariaText = ''"
      @change="toggleOptOut"
    >
    </v-switch>
    <span class="sr-only" aria-live="assertive">{{ ariaText }}</span>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import {updateOptOut} from '@/api/course'

export default {
  name: 'ToggleOptOut',
  mixins: [Context],
  props: {
    ariaLabel: {
      required: false,
      type: String,
      default: undefined
    },
    beforeToggle: {
      default: () => {},
      required: false,
      type: Function
    },
    disabled: {
      required: false,
      type: Boolean
    },
    initialValue: {
      required: true,
      type: Boolean
    },
    instructorUid: {
      required: true,
      type: String
    },
    label: {
      required: false,
      type: String,
      default: ''
    },
    onToggle: {
      default: () => {},
      required: false,
      type: Function
    },
    sectionId: {
      required: true,
      type: String
    },
    termId: {
      required: true,
      type: String
    }
  },
  data: () => ({
    ariaText: '',
    optOut: undefined,
    switchId: undefined
  }),
  created() {
    this.optOut = this.initialValue
    if (this.sectionId === 'all') {
      this.switchId = this.termId === 'all' ? 'all-terms' : 'current-term'
    } else {
      this.switchId = this.sectionId
    }
  },
  methods: {
    toggleOptOut() {
      this.ariaText = this.optOut ? 'on' : 'off'
      this.beforeToggle()
      updateOptOut(this.instructorUid, this.termId, this.sectionId, this.optOut).then(data => {
        this.onToggle(`Opted ${data.optedOut ? 'out' : 'in'} ${this.label}`)
      })
    }
  }
}
</script>
