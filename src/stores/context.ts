import mitt from 'mitt'
import {defineStore} from 'pinia'
import {get, toString} from 'lodash'
import {useTheme} from 'vuetify/framework'
import type {Handler} from 'mitt'
import type {DiabloConfig, DiabloUser, ScreenReaderAlert} from '@/lib/types'
import {ANONYMOUS_USER, putFocusNextTick} from '@/lib/utils'
import router from '@/router'

export const useContextStore = defineStore('context', {
  state: () => ({
    eventHub: mitt(),
    loading: false,
    screenReaderAlert: {
      message: '',
      politeness: 'polite'
    } as ScreenReaderAlert,
    snackbar: {
      color: 'primary' as string | undefined,
      text: undefined as string | undefined,
      timeout: -1 as number,
    },
    snackbarShow: false as boolean,
    currentUser: ANONYMOUS_USER as DiabloUser,
    config: {} as DiabloConfig,
  }),

  actions: {
    broadcast(eventType, data?) {
      this.eventHub.emit(eventType, data)
    },
    loadingStart(title?: string) {
      const route = router.currentRoute.value
      const pageTitle: string = title || toString(get(route, 'name'))
      this.loading = true
      this.screenReaderAlert = {
        message: `Loading ${pageTitle} page.`,
        politeness: 'polite'
      }
    },
    loadingComplete(title?: string, srAlert?: string) {
      const route = router.currentRoute.value
      const pageTitle: string = title || toString(get(route, 'name'))
      document.title = `${pageTitle ? pageTitle : 'Welcome'} | Course Capture`
      this.loading = false
      this.screenReaderAlert = {
        message: `${pageTitle || String(get(route, 'name', ''))} page loaded. ${srAlert || ''}`,
        politeness: 'polite'
      }
      putFocusNextTick('page-title')
    },
    alertScreenReader(message: string, politeness?: string) {
      this.screenReaderAlert = {
        message: message,
        politeness: politeness || 'polite'
      }
    },
    removeEventHandler(type: string, handler?: Handler) {
      this.eventHub.off(type, handler)
    },
    setEventHandler(type: string, handler: Handler) {
      this.eventHub.on(type, handler)
    },
    snackbarClose() {
      this.snackbarShow = false
      this.snackbar.text = undefined
      this.screenReaderAlert = {
        message: 'Message closed',
        politeness: 'polite'
      }
    },
    snackbarOpen(text: string) {
      this.snackbar.text = text
      this.snackbar.color = 'primary'
      this.snackbarShow = true
    },
    snackbarReportError(text: string) {
      this.snackbar.text = text
      this.snackbar.color = 'error'
      this.snackbarShow = true
    },
    setConfig(data: DiabloConfig) {
      this.config = data
    },
    setCurrentUser(user: DiabloUser) {
      this.currentUser = user
      useTheme().change(this.currentUser.prefersDarkMode ? 'dark' : 'light')
    }
  }
})
