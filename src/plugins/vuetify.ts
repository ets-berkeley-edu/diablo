import './main.scss'
import {aliases, mdi} from 'vuetify/iconsets/mdi-svg'
import {red} from 'vuetify/lib/util/colors'
import {createVuetify} from 'vuetify'
import {DatePicker} from 'v-calendar'
import {EditorContent} from '@tiptap/vue-3'
import {VApp} from 'vuetify/components/VApp'
import {VAppBar} from 'vuetify/components/VAppBar'
import {VBanner} from 'vuetify/components/VBanner'
import {VBottomSheet} from 'vuetify/components/VBottomSheet'
import {VBtn} from 'vuetify/components/VBtn'
import {VCard, VCardActions, VCardSubtitle, VCardText, VCardTitle} from 'vuetify/components/VCard'
import {VChip} from 'vuetify/components/VChip'
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
import {VSheet} from 'vuetify/components/VSheet'
import {VAlert, VAutocomplete, VListItemSubtitle, VSnackbar, VSwitch} from 'vuetify/components'
import {VTable} from 'vuetify/components/VTable'
import {VTextField} from 'vuetify/components/VTextField'
import {VTooltip} from 'vuetify/components/VTooltip'
import {VDivider} from 'vuetify/components/VDivider'
import {VTextarea} from 'vuetify/components/VTextarea'

export default createVuetify({
  components: {
    DatePicker,
    EditorContent,
    VApp,
    VAppBar,
    VAlert,
    VAutocomplete,
    VBanner,
    VBottomSheet,
    VBtn,
    VCard,
    VCardActions,
    VCardSubtitle,
    VCardText,
    VCardTitle,
    VChip,
    VCol,
    VContainer,
    VDataTable,
    VDialog,
    VDivider,
    VFooter,
    VForm,
    VIcon,
    VLayout,
    VList,
    VListItem,
    VListItemSubtitle,
    VListItemTitle,
    VMain,
    VMenu,
    VNavigationDrawer,
    VPagination,
    VProgressCircular,
    VRow,
    VSelect,
    VSheet,
    VSnackbar,
    VSpacer,
    VSwitch,
    VTable,
    VTextField,
    VTextarea,
    VTooltip
  },
  defaults: {
    VDataTable: {
      hover: true
    },
    VSelect: {
      density: 'comfortable',
      variant: 'underlined'
    },
    VTable: {
      hover: true
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
          anchor: '#ca4f16',
          black: '#000',
          error: red.accent3,
          primary: '#378dc5',
          secondary: '#68acd8',
          success: '#3a833c',
          'body-background': '#fff',
          'header-background': '#2a5f83',
          'icon-nav-dark-mode': '#2a5f83',
          'icon-nav-default': '#fff',
          'surface-light': '#f6f6f6',
          'table-border': '#979797',
          'tertiary': '#378dc5',
        }
      },
      dark: {
        colors: {
          accent: '#0d202c',
          anchor: '#ff5405',
          black: '#fff',
          error: '#ff6262',
          primary: '#58A0D0',
          secondary: '#2a5f83',
          'body-background': '#0d202c',
          'header-background': '#122b3c',
          'icon-nav-dark-mode': '#2a5f83',
          'icon-nav-default': '#378dc5',
          'surface-light': '#303030',
          'table-border': '#378dc5',
          'tertiary': '#173c55',
        }
      }
    }
  }
})
