import _ from 'lodash'
import App from './App.vue'
import axios from 'axios'
import core from './core';
import router from './router'
import store from './store'
import Vue from 'vue'
import vuetify from './plugins/vuetify'

const apiBaseUrl = process.env.VUE_APP_API_BASE_URL

axios.interceptors.response.use(response => response, function(error) {
  if (_.get(error, 'response.status') === 401) {
    axios.get(`${apiBaseUrl}/api/user/my_profile`).then(response => {
      Vue.prototype.$currentUser = response.data;
      Vue.prototype.$core.initializeCurrentUser().then(router.push({ path: '/login' }).catch(() => null));
    });
  }
  return Promise.reject(error);
});

// Allow cookies in Access-Control requests
axios.defaults.withCredentials = true

Vue.config.productionTip = false

// Lodash
Vue.prototype.$_ = _

// Emit, and listen for, events via hub
Vue.prototype.$eventHub = new Vue()

axios.get(`${apiBaseUrl}/api/user/my_profile`).then(response => {
  Vue.prototype.$currentUser = response.data

  axios.get(`${apiBaseUrl}/api/config`).then(response => {
    Vue.prototype.$config = response.data
    Vue.prototype.$config.apiBaseUrl = apiBaseUrl
    Vue.prototype.$config.isVueAppDebugMode = _.trim(process.env.VUE_APP_DEBUG).toLowerCase() === 'true'

    new Vue({
      router,
      store,
      vuetify,
      render: h => h(App),
    }).$mount('#app')

    Vue.prototype.$core = core;
    Vue.prototype.$core.initializeCurrentUser().then(_.noop);
  })
})
