// src/api/auth.ts
import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'
import {useContextStore} from '@/stores/context'


export async function devAuthLogIn(uid: string, password: string) {
  const store = useContextStore()
  const response = await axios.post(
    `${getApiBaseUrl()}/api/auth/dev_auth_login`,
    {uid, password}
  )
  const user = response.data
  // Update Pinia stores'stores currentUser
  store.setCurrentUser(user)
  return user
}

export function getCasLoginURL() {
  return axios.get(`${getApiBaseUrl()}/api/auth/cas_login_url`)
    .then(response => response.data)
}

export function getCasLogoutUrl() {
  return axios.get(`${getApiBaseUrl()}/api/auth/logout`)
    .then(response => response.data)
}
