import axios from 'axios'
import fileDownload from 'js-file-download'
import {getApiBaseUrl} from '@/api/api-utils'

export function downloadKalturaEvents(startDate: string, endDate: string) {
  const filename = `iCal_export_${startDate.replaceAll('-', '')}-${endDate.replaceAll('-', '')}.zip`
  const url = `${getApiBaseUrl()}/api/rooms/download_events`
  return axios.post(url, {startDate, endDate}, {responseType: 'blob'})
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

export function getKalturaEventList(kalturaResourceId: number) {
  return axios.get(`${getApiBaseUrl()}/api/room/${kalturaResourceId}/kaltura_events`)
    .then(response => response.data)
}

export function getRoom(id: number) {
  return axios.get(`${getApiBaseUrl()}/api/room/${id}`)
    .then(response => response.data)
}

export function updateRoomCapability(roomId: number, capability: string) {
  return axios.post(`${getApiBaseUrl()}/api/room/update_capability`, {
    roomId,
    capability
  })
}
