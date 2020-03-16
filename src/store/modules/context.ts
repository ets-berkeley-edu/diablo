import Vue from 'vue'

const state = {
  loading: undefined,
  screenReaderAlert: undefined
}

const getters = {
  loading: (state: any): boolean => state.loading,
  screenReaderAlert: (state: any): string => state.screenReaderAlert
}

const mutations = {
  loadingComplete: (state: any) => (state.loading = false),
  loadingStart: (state: any) => (state.loading = true),
  setScreenReaderAlert: (state: any, alert: any) => (state.screenReaderAlert = alert)
}

const actions = {
  loadingComplete: ({ commit }) => commit('loadingComplete'),
  loadingStart: ({ commit }) => commit('loadingStart'),
  setScreenReaderAlert: ({ commit }, alert) => {
    commit('setScreenReaderAlert', '')
    Vue.nextTick(() => commit('setScreenReaderAlert', alert))
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
