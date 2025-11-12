import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'
import {useContextStore} from '@/stores/context'

export function deleteUserNote(uid: string) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/note/delete`)
    .then(response => response.data)
}

export function getAdminUsers() {
  return axios.get(`${getApiBaseUrl()}/api/users/admins`)
    .then(response => response.data)
}

export function getCurrentUser() {
  return axios.get(`${getApiBaseUrl()}/api/user/my_profile`)
    .then(response => response.data)
}

export function getUser(uid: string) {
  return axios.get(`${getApiBaseUrl()}/api/user/${uid}`)
    .then(response => response.data)
}

export function searchUsers(snippet: string) {
  return axios.post(`${getApiBaseUrl()}/api/users/search`, {snippet})
    .then(response => response.data)
}

export function getCanvasSitesTeaching(uid: string) {
  return axios.get(`${getApiBaseUrl()}/api/user/${uid}/teaching_sites`)
    .then(response => response.data)
}

export function updateUserNote(uid: string, body: string) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/note/update`, {body})
    .then(response => response.data)
}

export function updateDoNotEmail(uid: string, doNotEmail: boolean) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/do_not_email/update`, {doNotEmail})
    .then(response => response.data)
}

export function updatePrefersDarkMode(prefersDarkMode: boolean) {
  return axios.post(`${getApiBaseUrl()}/api/user/prefers_dark_mode/update`, {prefersDarkMode})
    .then(response => {
      getCurrentUser().then(useContextStore().setCurrentUser)
      return response.data
    })
}

export function updateOptInNewCourses(uid: string, optInNewCourses: boolean) {
  return axios
    .post(`${getApiBaseUrl()}/api/user/${uid}/opt_in_new_courses/update`, {optInNewCourses})
    .then(response => response.data)
}
