import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

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
