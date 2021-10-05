<template>
  <div class="pl-2 pt-4">
    <h1>
      <span v-if="is420" :class="classForH1">
        <v-icon
          aria-label="Play entertaining video clip (opens a new tab)"
          class="icon-padding"
          :color="$vuetify.theme.dark ? 'white' : 'primary'"
          large
          @click="smile"
        >
          mdi-weather-tornado
        </v-icon> <span :class="clazz()"> {{ text }}</span>
      </span>
      <span v-if="!is420">
        <v-icon
          class="icon-padding"
          :color="$vuetify.theme.dark ? 'white' : 'primary'"
          large
        >
          {{ icon }}
        </v-icon> <span id="page-title" :class="clazz()" tabindex="0"> {{ text }}</span>
      </span>
    </h1>
  </div>
</template>

<script>
export default {
  name: 'PageTitle',
  props: {
    classForH1: {
      default: undefined,
      required: false,
      type: String
    },
    icon: {
      required: true,
      type: String
    },
    text: {
      required: true,
      type: String
    }
  },
  data: () => ({
    is420: undefined
  }),
  created() {
    this.is420 = this.$moment().format('H:mm') === '16:20'
  },
  methods: {
    clazz() {
      return this.text.length > 40 ? `${this.classForH1} text-h4` : this.classForH1
    },
    smile() {
      window.open(this.$config.easterEgg420, '_blank')
    }
  }
}
</script>

<style scoped>
  .icon-padding {
    padding: 0 3px 4px 0;
  }
</style>
