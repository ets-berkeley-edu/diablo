import '@mdi/font/css/materialdesignicons.min.css'
import 'vuetify/dist/vuetify.min.css'
import {createApp} from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import axios from 'axios'
import _ from 'lodash'
import {DateTime} from 'luxon'

// UI plugins
import VCalendar from 'v-calendar'
import 'v-calendar/style.css'
import VWave from 'v-wave'

// Vuetify 3 setup
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import {createVuetify} from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const pinia = createPinia()
const vuetify = createVuetify({
  components,
  directives,
  theme: {defaultTheme: 'light'},
})

//
// — Axios global setup (same as before) —
//
axios.defaults.withCredentials = true
axios.interceptors.response.use(
  res => res.headers['content-type']?.includes('application/json') ? res.data : res,
  error => {
    // your error handler logic...
    return Promise.reject(error)
  }
)

//
// — Build the app —
//
const app = createApp(App)

// register core plugins
app.use(pinia)
app.use(router)
app.use(vuetify)

// register 3rd-party plugins
app.use(VCalendar, { componentPrefix: 'c' })
app.use(VWave, {})

// expose globals (was Vue.prototype)
app.config.globalProperties.$axios = axios
app.config.globalProperties.$_ = _
app.config.globalProperties.$DateTime = DateTime
// e.g.:
// app.config.globalProperties.$loading = () => pinia.store('context').loadingStart()
// app.config.globalProperties.$putFocusNextTick = (id, sel) => { /*...*/ }

app.mount('#app')
