import '@mdi/font/css/materialdesignicons.min.css'
import 'vuetify/dist/vuetify.min.css'
import {createApp} from 'vue'
import App from './App.vue'
import router from './router'
import {createPinia} from 'pinia'
import axios from 'axios'
import {trim} from 'lodash'
import axiosPlugin from '@/plugins/axios'
import {appErrorHandler, initializeAxios} from '@/lib/axios-utils'

import VCalendar from 'v-calendar'
import 'v-calendar/style.css'
import VWave from 'v-wave'
import {useContextStore} from '@/stores/context'

import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import {createVuetify} from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const apiBaseUrl: string = import.meta.env.VITE_APP_API_BASE_URL
const isVueAppDebugMode: boolean = trim(import.meta.env.VITE_APP_DEBUG).toLowerCase() === 'true'

const vuetify = createVuetify({
  components,
  directives,
  theme: {defaultTheme: 'light'},
})

const app = createApp(App)
app.config.errorHandler = appErrorHandler

app.use(createPinia())
  .use(axiosPlugin, {baseUrl: apiBaseUrl})
  .use(vuetify)
  .use(VCalendar, {componentPrefix: 'c'})
  .use(VWave, {})

initializeAxios(axios)

axios.get(`${apiBaseUrl}/api/config`).then(response => {
  useContextStore().setConfig({...response.data, apiBaseUrl, isVueAppDebugMode})
  axios.get(`${apiBaseUrl}/api/user/my_profile`).then(response => {
    useContextStore().setCurrentUser(response.data)
    app.use(router).mount('#app')
  })
})
