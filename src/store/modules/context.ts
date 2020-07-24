import Vue from 'vue'

const state = {
  loading: undefined,
  screenReaderAlert: undefined,
  snackbar: {
    color: 'primary',
    text: undefined,
    timeout: 8000
  },
  snackbarShow: false
}

const getters = {
  loading: (state: any): boolean => state.loading,
  screenReaderAlert: (state: any): string => state.screenReaderAlert,
  snackbar: (state: any): any => state.snackbar,
  snackbarShow: (state: any): boolean => state.snackbarShow,
}

const mutations = {
  loadingComplete: (state: any, pageTitle: string) => {
    document.title = `${pageTitle || 'UC Berkeley'} | Course Capture`
    state.loading = false
    if (pageTitle) {
      state.screenReaderAlert = `${pageTitle} page is ready`
    }
    Vue.prototype.$putFocusNextTick('page-title')
  },
  loadingStart: (state: any) => (state.loading = true),
  setScreenReaderAlert: (state: any, alert: string) => (state.screenReaderAlert = alert),
  snackbarClose: (state: any) => {
    state.snackbarShow = false
    state.snackbar.text = undefined
    state.screenReaderAlert = 'Message closed'
  },
  snackbarOpen: (state: any, text) => {
    state.snackbar.text = text
    state.snackbar.color = 'primary'
    state.snackbarShow = true
  },
  snackbarReportError: (state: any, text) => {
    state.snackbar.text = text
    state.snackbar.color = 'error'
    state.snackbarShow = true
  }
}

const actions = {
  alertScreenReader: ({ commit }, alert) => commit('setScreenReaderAlert', alert),
  loadingComplete: ({ commit }, pageTitle) => commit('loadingComplete', pageTitle),
  loadingStart: ({ commit }) => commit('loadingStart'),
  snackbarClose: ({ commit }) => commit('snackbarClose'),
  snackbarOpen: ({ commit }, text) => commit('snackbarOpen', text),
  snackbarReportError: ({ commit }, text) => commit('snackbarReportError', text)
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
