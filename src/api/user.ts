import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function deleteUserNote(uid: string) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/note/delete`)
    .then(response => response.data)
}

export function getAdminUsers() {
  return axios.get(`${getApiBaseUrl()}/api/users/admins`)
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

export function updateDoNotEmail(uid: string, body: { doNotEmail: boolean }) {
  return axios.post(`${getApiBaseUrl()}/api/user/${uid}/do_not_email/update`, body)
    .then(response => response.data)
}

export function updateOptInNewCourses(
  uid: string, payload: { optInNewCourses: boolean }
) {
  return axios
    .post(`${getApiBaseUrl()}/api/user/${uid}/opt_in_new_courses/update`, payload)
    .then(response => response.data)
}
