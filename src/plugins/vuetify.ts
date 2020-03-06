import colors from 'vuetify/lib/util/colors'
import Vue from 'vue'
import Vuetify from 'vuetify/lib'

Vue.use(Vuetify)

export default new Vuetify( {
  theme: {
    themes: {
      light: {
        primary: colors.purple.lighten1,
        secondary: colors.grey.darken1,
        accent: colors.shades.black,
        error: colors.red.accent3,
      },
      dark: {
        primary: colors.purple.lighten1,
      }
    }
  }
})
