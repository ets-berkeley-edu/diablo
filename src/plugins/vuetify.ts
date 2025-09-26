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
import {VExpandTransition} from 'vuetify/components/transitions'
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
import {VRadio} from 'vuetify/components/VRadio'
import {VRadioGroup} from 'vuetify/components/VRadioGroup'
import {VCheckbox} from 'vuetify/components/VCheckbox'

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
    VCheckbox,
    VChip,
    VCol,
    VContainer,
    VDataTable,
    VDialog,
    VDivider,
    VExpandTransition,
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
    VRadio,
    VRadioGroup,
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
          accent: '#f44336',
          anchor: '#ca4f16',
          banner: '#224f6e',
          error: red.accent4,
          'icon-nav': '#fff',
          primary: '#307aab',
          secondary: '#347cad',
          success: '#3a833c',
          'surface-light': '#f6f6f6',
          'table-border': '#c9c9c9',
          tertiary: '#27658e',
           warning: '#b36200'
        }
      },
      dark: {
        colors: {
          accent: red.accent3,
          anchor: '#ff702e',
          banner: '#122b3c',
          error: '#ff6262',
          'icon-nav': '#378dc5',
          primary: '#307aab',
          secondary: '#2a5f83',
          'surface-light': '#303030',
          'table-border': '#378dc5',
          tertiary: '#173c55',
        }
      }
    }
  }
})
