import 'tiptap-vuetify/dist/main.css'
import 'vuetify/dist/vuetify.min.css'
import _ from 'lodash'
import App from './App.vue'
import axios from 'axios'
import core from './core'
import moment from 'moment-timezone'
import router from './router'
import store from './store'
import { TiptapVuetifyPlugin } from 'tiptap-vuetify'
import Vue from 'vue'
import VueMoment from 'vue-moment'
import vuetify from './plugins/vuetify'

Vue.use(TiptapVuetifyPlugin, {
  vuetify,
  iconsGroup: 'md'
})
Vue.use(VueMoment, { moment })

const apiBaseUrl = process.env.VUE_APP_API_BASE_URL
const isDebugMode = _.trim(process.env.VUE_APP_DEBUG).toLowerCase() === 'true'

// Axios
axios.defaults.withCredentials = true
axios.interceptors.response.use(
    response => {
      return response.data
    },
    error => {
      const errorStatus = _.get(error, 'response.status')
      if (_.get(Vue.prototype.$currentUser, 'isAuthenticated')) {
        if (errorStatus === 404) {
          router.push({ path: '/404' })
        } else if (errorStatus >= 400) {
          const message = _.get(error, 'response.data.message') || error.message
          console.error(message)
          router.push({
            path: '/error',
            query: {
              m: message
            }
          })
        }
      } else {
        // Raise error and let /login page display the message
        throw _.get(error, 'response.data.message') || `Error: Server responded with status ${errorStatus}`
      }
    })

// Vue config
Vue.config.productionTip = isDebugMode
Vue.config.errorHandler = function(error, vm, info) {
  console.error(error || info)
  router.push({
    path: '/error',
    query: {
      m: _.get(error, 'message') || info
    }
  })
}

// Vue prototype
Vue.prototype.$_ = _
Vue.prototype.$eventHub = new Vue()
Vue.prototype.$loading = () => store.dispatch('context/loadingStart')
Vue.prototype.$ready = () => store.dispatch('context/loadingComplete')

axios.get(`${apiBaseUrl}/api/user/my_profile`).then(data => {
  Vue.prototype.$currentUser = data

  axios.get(`${apiBaseUrl}/api/config`).then(data => {
    Vue.prototype.$config = data
    Vue.prototype.$config.apiBaseUrl = apiBaseUrl
    Vue.prototype.$config.isVueAppDebugMode = isDebugMode

    new Vue({
      router,
      store,
      vuetify,
      render: h => h(App),
    }).$mount('#app')

    Vue.prototype.$core = core
    Vue.prototype.$core.initializeCurrentUser().then(_.noop)
  })
})
