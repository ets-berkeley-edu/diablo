<template>
  <div class="pl-2 pt-1">
    <h1>
      <v-icon
        class="pb-1 pr-1"
        :color="$vuetify.theme.dark ? 'white' : 'primary'"
        large
        @click="is420 ? sharknado() : $_.noop"
      >
        {{ is420 ? 'mdi-weather-tornado' : icon }}
      </v-icon> {{ text }}
    </h1>
  </div>
</template>

<script>
  export default {
    name: 'PageTitle',
    props: {
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
      sharknado() {
        window.open(this.$config.easterEgg420, '_blank')
      }
    }
  }
</script>
