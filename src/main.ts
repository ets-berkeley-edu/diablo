import '@mdi/font/css/materialdesignicons.min.css'
import 'vuetify/dist/vuetify.min.css'
import {createApp} from 'vue'
import App from './App.vue'
import router from './router'
import {createPinia} from 'pinia'
import axios from 'axios'
import _ from 'lodash'
import {DateTime} from 'luxon'

import VCalendar from 'v-calendar'
import 'v-calendar/style.css'
import VWave from 'v-wave'

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


axios.defaults.withCredentials = true
axios.interceptors.response.use(
  res => res.headers['content-type']?.includes('application/json') ? res.data : res,
  error => {
    return Promise.reject(error)
  }
)


const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)

app.use(VCalendar, {componentPrefix: 'c'})
app.use(VWave, {})

app.config.globalProperties.$axios = axios
app.config.globalProperties.$_ = _
app.config.globalProperties.$DateTime = DateTime

app.mount('#app')
