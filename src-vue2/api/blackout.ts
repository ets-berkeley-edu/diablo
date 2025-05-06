import axios from 'axios'
import utils from '@/api/api-utils'

export function createBlackout(name, startDate, endDate) {
  return axios.post(`${utils.apiBaseUrl()}/api/blackout/create`, {
    name,
    startDate,
    endDate
  })
}

export function deleteBlackout(bookmarkId) {
  return axios.delete(`${utils.apiBaseUrl()}/api/blackout/${bookmarkId}`)
}

export function getAllBlackouts() {
  return axios.get(`${utils.apiBaseUrl()}/api/blackouts/all`)
}

export function getBlackout(bookmarkId: number) {
  return axios.get(`${utils.apiBaseUrl()}/api/blackout/${bookmarkId}`)
}

export function updateBlackout(bookmarkId, name, startDate, endDate) {
  return axios.post(`${utils.apiBaseUrl()}/api/blackout/update`, {
    bookmarkId,
    name,
    startDate,
    endDate
  })
}
