import colors from 'vuetify/lib/util/colors'
import Vue from 'vue'
import Vuetify from 'vuetify/lib'

Vue.use(Vuetify)

export default new Vuetify( {
  theme: {
    themes: {
      light: {
        primary: '#378dc5',
        secondary: '#68acd8',
        accent: '#2a5f83',
        error: colors.red.accent3,
        'body-background': '#fff',
        'header-background': '#2a5f83',
        'icon-nav-dark-mode': '#2a5f83',
        'icon-nav-default': '#fff',
        'nav-background': '#378dc5',
        'table-border': '#979797'
      },
      dark: {
        primary: '#173c55',
        secondary: '#2a5f83',
        accent: '#0d202c',
        error: colors.red.accent3,
        'body-background': '#0d202c',
        'header-background': '#122b3c',
        'icon-nav-dark-mode': '#2a5f83',
        'icon-nav-default': '#378dc5',
        'nav-background': '#173c55',
        'table-border': '#378dc5'
      }
    }
  }
})
