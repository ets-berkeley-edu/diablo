import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function deleteUserNote(uid) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/note/delete`)
    .then(response => response.data)
}

export function getAdminUsers() {
  return axios.get(`${getApiBaseUrl()}/api/users/admins`)
    .then(response => response.data)
}

export function getCalnetUser(uid) {
  return axios.get(`${getApiBaseUrl()}/api/user/${uid}/calnet`)
    .then(response => response.data)
}

export function getUser(uid) {
  return axios.get(`${getApiBaseUrl()}/api/user/${uid}`)
    .then(response => response.data)
}

export function searchUsers(snippet: string) {
  return axios.post(`${getApiBaseUrl()}/api/users/search`, {snippet})
    .then(response => response.data)
}

export function getCanvasSitesTeaching(uid) {
  return axios.get(`${getApiBaseUrl()}/api/user/${uid}/teaching_sites`)
    .then(response => response.data)
}

export function updateUserNote(uid, body: string) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/note/update`, {body})
    .then(response => response.data)
}
