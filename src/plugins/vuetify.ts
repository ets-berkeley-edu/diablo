import './main.scss'
import {aliases, mdi} from 'vuetify/iconsets/mdi-svg'
import colors from 'vuetify/lib/util/colors'
import {createVuetify} from 'vuetify'
import {DatePicker} from 'v-calendar'
import {VApp} from 'vuetify/components/VApp'
import {VAppBar} from 'vuetify/components/VAppBar'
import {VBanner} from 'vuetify/components/VBanner'
import {VBtn} from 'vuetify/components/VBtn'
import {VCard, VCardActions, VCardSubtitle, VCardText, VCardTitle} from 'vuetify/components/VCard'
import {VCol, VContainer, VRow, VSpacer} from 'vuetify/components/VGrid'
import {VDataTable} from 'vuetify/components/VDataTable'
import {VDialog} from 'vuetify/components/VDialog'
import {VFooter} from 'vuetify/components/VFooter'
import {VForm} from 'vuetify/components/VForm'
import {VIcon} from 'vuetify/components/VIcon'
import {VLayout} from 'vuetify/components/VLayout'
import {VList, VListItem, VListItemTitle} from 'vuetify/components/VList'
import {VMain} from 'vuetify/components/VMain'
import {VMenu} from 'vuetify/components/VMenu'
import {VNavigationDrawer} from 'vuetify/components/VNavigationDrawer'
import {VPagination} from 'vuetify/components/VPagination'
import {VProgressCircular} from 'vuetify/components/VProgressCircular'
import {VSelect} from 'vuetify/components/VSelect'
import {VSnackbar, VSwitch} from 'vuetify/components'
import {VTable} from 'vuetify/components/VTable'
import {VTextField} from 'vuetify/components/VTextField'
import {VTooltip} from 'vuetify/components/VTooltip'


export default createVuetify({
  components: {
    DatePicker,
    VApp,
    VAppBar,
    VBanner,
    VBtn,
    VCard,
    VCardActions,
    VCardSubtitle,
    VCardText,
    VCardTitle,
    VCol,
    VContainer,
    VDataTable,
    VDialog,
    VFooter,
    VForm,
    VIcon,
    VLayout,
    VList,
    VListItem,
    VListItemTitle,
    VMain,
    VMenu,
    VNavigationDrawer,
    VPagination,
    VProgressCircular,
    VRow,
    VSelect,
    VSnackbar,
    VSpacer,
    VSwitch,
    VTable,
    VTextField,
    VTooltip
  },
  defaults: {
    VSelect: {
      density: 'comfortable',
      variant: 'underlined'
    },
    VTextField: {
      density: 'comfortable',
      variant: 'underlined'
    }
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi
    }
  },
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
          'sidebar': '#378dc5',
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
          'sidebar': '#173c55',
          'table-border': '#378dc5'
        }
      }
    }
  }
})
