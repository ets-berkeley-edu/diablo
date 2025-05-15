import axios from 'axios'
import utils from '@/api/api-utils'

export function deleteUserNote(uid) {
  return axios.post(`${utils.apiBaseUrl()}/api/user/${uid}/note/delete`)
}

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

export function getCanvasSitesTeaching(uid) {
  return axios.get(`${utils.apiBaseUrl()}/api/user/${uid}/teaching_sites`)
}

export function updateUserNote(uid, body: string) {
  return axios.post(`${utils.apiBaseUrl()}/api/user/${uid}/note/update`, {body})
}
