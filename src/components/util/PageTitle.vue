<template>
  <div class="pl-2 pt-4">
    <h1 id="page-title" tabindex="-1">
      <div v-if="is420" class="d-flex align-center" :class="classForH1">
        <v-icon
          aria-label="Play entertaining video clip (opens a new tab)"
          class="mr-3"
          :color="$vuetify.theme.dark ? 'white' : 'primary'"
          size="36"
          @click="smile"
        >
          mdi-weather-tornado
        </v-icon>
        <span :class="clazz()"> {{ text }}</span>
      </div>
      <div v-if="!is420" class="d-flex align-center">
        <v-icon
          class="mr-3"
          :color="$vuetify.theme.dark ? 'white' : 'primary'"
          size="36"
        >
          {{ icon }}
        </v-icon>
        <span :class="clazz()" tabindex="-1"> {{ text }}</span>
      </div>
    </h1>
    <div v-if="subTitle" class="ml-5 pl-8 text-subtitle-1 text-primary">
      {{ subTitle }}
    </div>
  </div>
</template>

<script>
import {DateTime} from 'luxon'

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
    subTitle: {
      default: undefined,
      required: false,
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
    this.is420 = DateTime.now().toFormat('H:mm') === '16:20'
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
