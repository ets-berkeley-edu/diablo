import axios from 'axios'
import fileDownload from 'js-file-download'
import {getApiBaseUrl} from '@/api/api-utils'
import type {Room} from '@/lib/types'

const _sanitize_filename = (filename: string) => {
  return filename.replace(/['’/\\?%*:|"<>.,;=]/g, '').replaceAll(' ', '_')
}

export function downloadKalturaEvents(room: Room, startDate: string, endDate: string) {
  let filename: string, uri: string
  const postData = {startDate, endDate}
  if (room) {
    filename = `${_sanitize_filename(room.location)}_${startDate.replaceAll('-', '')}-${endDate.replaceAll('-', '')}.ics`
    uri = 'api/room/download_events'
    postData['roomId'] = room.id
  } else {
    filename = `iCal_export_${startDate.replaceAll('-', '')}-${endDate.replaceAll('-', '')}.zip`
    uri = 'api/rooms/download_events'
  }
  return axios.post(`${getApiBaseUrl()}/${uri}`, postData, {responseType: 'blob'})
  .then(response => fileDownload(response.data, filename))
  .catch(error => {
    return new Promise((resolve, reject) => {
      return error.response.data.text().then((text: string) => {
        let message: string
        try {
          message = JSON.parse(text).message
        } catch {
          message = 'An unknown error occurred.'
        }
        return reject(message)
      })
    })
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
