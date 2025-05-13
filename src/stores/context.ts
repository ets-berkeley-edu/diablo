import {defineStore} from 'pinia'
import {putFocusNextTick} from '@/lib/utils'

export type DiabloConfig = {
  apiBaseUrl: string,
  devAuthEnabled: boolean,
  currentTermName: string,
  currentTermId: number,
  canvasBaseUrl: string,
  kalturaMediaSpaceUrl: string,
  searchItemsPerPage: number,
  isVueAppDebugMode: boolean,
  emailCourseCaptureSupport: string,
  currentTermRecordingsBegin: any,
  currentTermRecordingsEnd: any,
  searchFilterOptions: any,
  emailTemplateTypes: any,
  courseCaptureExplainedUrl: string,
  uxBannerColor: any
}

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
    currentUser: {
      uid: undefined as string | undefined,
      departments: [] as any[],
      isAdmin: false,
      isAuthenticated: false,
      isTeaching: false,
      courses: [] as any[]
    },
    config: {} as DiabloConfig,
  }),

  actions: {
    loadingStart(srAlert?: string) {
      this.loading = true
      // TODO: uncomment once Context mixin is gone
      // const route = router.currentRoute.value
      this.screenReaderAlert = srAlert // || `Loading ${String(get(route, 'name', ''))}.`
    },
    loadingComplete(pageTitle?: string) {
      document.title = `${pageTitle || 'UC Berkeley'} | Course Capture`
      this.loading = false
      if (pageTitle) {
        this.screenReaderAlert = `${pageTitle} loading`
      }
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
      console.log('this.currentuser', this.currentUser)
    },

  }
})
