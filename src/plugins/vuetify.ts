import colors from 'vuetify/lib/util/colors'
import {createVuetify} from 'vuetify'

export default createVuetify({
  theme: {
    themes: {
      light: {
        colors: {
          accent: '#2a5f83',
          black: '#000',
          error: colors.red.accent3,
          primary: '#378dc5',
          secondary: '#68acd8',
          'body-background': '#fff',
          'header-background': '#2a5f83',
          'icon-nav-dark-mode': '#2a5f83',
          'icon-nav-default': '#fff',
          'nav-background': '#378dc5',
          'table-border': '#979797'
        }
      },
      dark: {
        colors: {
          accent: '#0d202c',
          black: '#fff',
          error: colors.red.accent3,
          primary: '#58A0D0',
          secondary: '#2a5f83',
          'body-background': '#0d202c',
          'header-background': '#122b3c',
          'icon-nav-dark-mode': '#2a5f83',
          'icon-nav-default': '#378dc5',
          'nav-background': '#173c55',
          'table-border': '#378dc5'
        }
      }
    }
  }
})
