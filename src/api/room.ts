import axios from 'axios'
import fileDownload from 'js-file-download'
import {get} from 'lodash'
import {getApiBaseUrl} from '@/api/api-utils'

const _sanitize_filename = (filename: string) => {
  return filename.replace(/[/\\?%*:|"<>.,;=]/g, '').replaceAll(' ', '_')
}
export function downloadKalturaEvents(roomId: number, location: string, startDate: string, endDate: string) {
  const filename = `${_sanitize_filename(location)}_${startDate.replaceAll('-', '')}-${endDate.replaceAll('-', '')}.ics`
  return axios.post(`${getApiBaseUrl()}/api/room/download_events`, {
    roomId,
    startDate,
    endDate
  }).then(response => {
    if (get(response.data, 'message')) {
      return Promise.reject(response.data.message)
    } else {
      return fileDownload(response.data, filename)
    }
  })
}

export function getAllRooms() {
  return axios.get(`${getApiBaseUrl()}/api/rooms/all`)
    .then(response => response.data)
}

export function getAuditoriums() {
  return axios.get(`${getApiBaseUrl()}/api/rooms/auditoriums`)
    .then(response => response.data)
}

export function getKalturaEventList(kalturaResourceId: number) {
  return axios.get(`${getApiBaseUrl()}/api/room/${kalturaResourceId}/kaltura_events`)
    .then(response => response.data)
}

export function getRoom(id: number) {
  return axios.get(`${getApiBaseUrl()}/api/room/${id}`)
    .then(response => response.data)
}

export function setAuditorium(roomId: number, isAuditorium: boolean) {
  return axios.post(`${getApiBaseUrl()}/api/room/auditorium`, {
    roomId,
    isAuditorium
  })
}

export function updateRoomCapability(roomId: number, capability: string) {
  return axios.post(`${getApiBaseUrl()}/api/room/update_capability`, {
    roomId,
    capability
  })
}
