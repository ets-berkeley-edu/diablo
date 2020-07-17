<template>
  <div class="pl-2 pt-4">
    <h1>
      <v-icon
        class="icon-padding"
        :color="$vuetify.theme.dark ? 'white' : 'primary'"
        large
        @click="is420 ? sharknado() : $_.noop"
      >
        {{ is420 ? 'mdi-weather-tornado' : icon }}
      </v-icon> <span :class="{'text-h4': text.length > 40}"> {{ text }}</span>
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

<style scoped>
  .icon-padding {
    padding: 0 3px 4px 0;
  }
</style>
