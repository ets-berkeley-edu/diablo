import axios from 'axios'
import utils from '@/api/api-utils'

export function getUser(uid) {
  return axios.get(`${utils.apiBaseUrl()}/api/user/${uid}`)
}

export function getCalnetUser(uid) {
  return axios.get(`${utils.apiBaseUrl()}/api/user/${uid}/calnet`)
}

export function getAdminUsers() {
  return axios.get(`${utils.apiBaseUrl()}/api/users/admins`)
}

export function searchUsers(snippet: string) {
  return axios.post(`${utils.apiBaseUrl()}/api/users/search`, {snippet})
}
