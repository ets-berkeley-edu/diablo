import Vue from 'vue'

export default {
  apiBaseUrl: () => Vue.prototype.$config.apiBaseUrl
}
