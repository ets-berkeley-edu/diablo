import axios from 'axios'
import utils from '@/api/api-utils'

export function getAllRooms() {
  return axios.get(`${utils.apiBaseUrl()}/api/rooms/all`)
}

export function getKalturaEventList(roomId) {
  return axios.get(`${utils.apiBaseUrl()}/api/room/${roomId}/kaltura_event_list`)
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
