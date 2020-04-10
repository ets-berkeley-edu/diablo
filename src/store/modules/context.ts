import Vue from 'vue'

const state = {
  loading: undefined,
  screenReaderAlert: undefined,
  snackbar: {
    color: 'primary',
    text: undefined,
    timeout: 2000
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
  loadingComplete: (state: any) => (state.loading = false),
  loadingStart: (state: any) => (state.loading = true),
  setScreenReaderAlert: (state: any, alert: any) => (state.screenReaderAlert = alert),
  snackbarClose: (state: any) => {
    state.snackbarShow = false
    state.snackbar.text = undefined
  },
  snackbarOpen: (state: any, text) => {
    state.snackbar.text = text
    state.snackbar.color = 'primary'
    state.snackbarShow = true
  }
}

const actions = {
  loadingComplete: ({ commit }) => commit('loadingComplete'),
  loadingStart: ({ commit }) => commit('loadingStart'),
  setScreenReaderAlert: ({ commit }, alert) => {
    commit('setScreenReaderAlert', '')
    Vue.nextTick(() => commit('setScreenReaderAlert', alert))
  },
  snackbarClose: ({ commit }) => commit('snackbarClose'),
  snackbarOpen: ({ commit }, text) => commit('snackbarOpen', text)
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
