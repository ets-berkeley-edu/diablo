import _ from 'lodash'
import axios from 'axios'
import utils from '@/api/api-utils'
import Vue from 'vue'

export function devAuthLogIn(uid: string, password: string) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/auth/dev_auth_login`, {
      uid: uid,
      password: password
    })
    .then(response => {
      Vue.prototype.$currentUser = response.data
      Vue.prototype.$core.initializeCurrentUser().then(_.noop)
      return Vue.prototype.$currentUser
    }, error => error)
}

export function getCasLoginURL() {
  return axios
    .get(`${utils.apiBaseUrl()}/api/auth/cas_login_url`)
    .then(response => response.data, () => null)
}

export function getCasLogoutUrl() {
  return axios
    .get(`${utils.apiBaseUrl()}/api/auth/logout`)
    .then(response => response.data, () => null)
}
