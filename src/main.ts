import App from './App.vue'
import VWave from 'v-wave'
import axios from 'axios'
import {createApp} from 'vue'
import {createPinia} from 'pinia'
import router from './router'
import {setupCalendar} from 'v-calendar'
import {trim} from 'lodash'
import {appErrorHandler, initializeAxios} from '@/lib/axios-utils'
import axiosPlugin from '@/plugins/axios'
import {getCurrentUser} from '@/api/auth'
import {useContextStore} from '@/stores/context'
import vuetify from '@/plugins/vuetify'

import '@mdi/font/css/materialdesignicons.css'

const apiBaseUrl: string = import.meta.env.VITE_APP_API_BASE_URL
const isVueAppDebugMode: boolean = trim(import.meta.env.VITE_APP_DEBUG).toLowerCase() === 'true'

const app = createApp(App)
app.config.errorHandler = appErrorHandler

app.use(createPinia())
  .use(axiosPlugin, {baseUrl: apiBaseUrl})
  .use(vuetify)
  .use(setupCalendar, {})
  .use(VWave, {})

initializeAxios(axios)

axios.get(`${apiBaseUrl}/api/config`).then(response => {
  useContextStore().setConfig({...response.data, apiBaseUrl, isVueAppDebugMode})
  getCurrentUser().then(user => {
    useContextStore().setCurrentUser(user)
    app.use(router).mount('#app')
  })
})
