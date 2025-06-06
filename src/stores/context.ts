import {defineStore} from 'pinia'
import {get} from 'lodash'
import type {DiabloConfig, DiabloUser} from '@/lib/types'
import {ANONYMOUS_USER, putFocusNextTick} from '@/lib/utils'
import router from '@/router'

export const useContextStore = defineStore('context', {
  state: () => ({
    loading: false,
    screenReaderAlert: undefined as string | undefined,
    snackbar: {
      color: 'primary' as string | undefined,
      text: undefined as string | undefined,
      timeout: 8000 as number,
    },
    snackbarShow: false as boolean,
    currentUser: ANONYMOUS_USER as DiabloUser,
    config: {} as DiabloConfig,
  }),

  actions: {
    loadingStart() {
      const route = router.currentRoute.value
      this.loading = true
      this.screenReaderAlert = `Loading ${String(get(route, 'name', ''))}.`
    },
    loadingComplete(pageTitle?: string, srAlert?: string) {
      const route = router.currentRoute.value
      this.loading = false
      this.screenReaderAlert = `${pageTitle || String(get(route, 'name', '')) || 'Page'} loaded. ${srAlert || ''}`
      putFocusNextTick('page-title')
    },
    alertScreenReader(message: string) {
      this.screenReaderAlert = message
    },
    snackbarClose() {
      this.snackbarShow = false
      this.snackbar.text = undefined
      this.screenReaderAlert = 'Message closed'
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
    setConfig(data: any) {
      this.config = data
    },
    setCurrentUser(user: any) {
      this.currentUser = user
    }
  }
})
