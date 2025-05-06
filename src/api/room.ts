import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function getAllRooms() {
  return axios.get(`${getApiBaseUrl()}/api/rooms/all`)
}

export function getAuditoriums() {
  return axios.get(`${getApiBaseUrl()}/api/rooms/auditoriums`)
}

export function getKalturaEventList(kalturaResourceId) {
  return axios.get(`${getApiBaseUrl()}/api/room/${kalturaResourceId}/kaltura_events`)
}

export function getRoom(id) {
  return axios.get(`${getApiBaseUrl()}/api/room/${id}`)
}

export function setAuditorium(roomId, isAuditorium) {
  return axios.post(`${getApiBaseUrl()}/api/room/auditorium`, {
    roomId,
    isAuditorium
  })
}

export function updateRoomCapability(roomId, capability) {
  return axios.post(`${getApiBaseUrl()}/api/room/update_capability`, {
    roomId,
    capability
  })
}
