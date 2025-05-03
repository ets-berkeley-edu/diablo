import axios from 'axios'
import utils from '@/api/api-utils'

export function getAllRooms() {
  return axios.get(`${utils.apiBaseUrl()}/api/rooms/all`)
}

export function getAuditoriums() {
  return axios.get(`${utils.apiBaseUrl()}/api/rooms/auditoriums`)
}

export function getKalturaEventList(kalturaResourceId) {
  return axios.get(`${utils.apiBaseUrl()}/api/room/${kalturaResourceId}/kaltura_events`)
}

export function getRoom(id) {
  return axios.get(`${utils.apiBaseUrl()}/api/room/${id}`)
}

export function setAuditorium(roomId, isAuditorium) {
  return axios.post(`${utils.apiBaseUrl()}/api/room/auditorium`, {
    roomId,
    isAuditorium
  })
}

export function updateRoomCapability(roomId, capability) {
  return axios.post(`${utils.apiBaseUrl()}/api/room/update_capability`, {
    roomId,
    capability
  })
}
