import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function createBlackout(name: string, startDate: string, endDate: string) {
  return axios.post(`${getApiBaseUrl()}/api/blackout/create`, {
    name,
    startDate,
    endDate
  })
}

export function deleteBlackout(bookmarkId: number) {
  return axios.delete(`${getApiBaseUrl()}/api/blackout/${bookmarkId}`)
    .then(response => response.data)
}

export function getAllBlackouts() {
  return axios.get(`${getApiBaseUrl()}/api/blackouts/all`)
    .then(response => response.data)
}

export function getBlackout(bookmarkId: number) {
  return axios.get(`${getApiBaseUrl()}/api/blackout/${bookmarkId}`)
    .then(response => response.data)
}

export function updateBlackout(bookmarkId, name, startDate, endDate) {
  return axios.post(`${getApiBaseUrl()}/api/blackout/update`, {
    bookmarkId,
    name,
    startDate,
    endDate
  })
}
