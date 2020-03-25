import axios from 'axios'
import utils from '@/api/api-utils'

export function getAllRooms() {
  return axios
      .get(`${utils.apiBaseUrl()}/api/rooms/all`)
      .then(response => response.data, () => null)
}

export function getCapabilityOptions() {
  return axios
      .get(`${utils.apiBaseUrl()}/api/rooms/capability_options`)
      .then(response => response.data, () => null)
}

export function getRoom(id) {
  return axios
      .get(`${utils.apiBaseUrl()}/api/room/${id}`)
      .then(response => response.data, () => null)
}

export function setAuditorium(roomId, isAuditorium) {
  return axios
      .post(`${utils.apiBaseUrl()}/api/room/auditorium`, {
        roomId,
        isAuditorium
      })
      .then(response => response.data, () => null)
}

export function updateRoomCapability(roomId, capability) {
  return axios
      .post(`${utils.apiBaseUrl()}/api/room/update_capability`, {
        roomId,
        capability
      })
      .then(response => response.data, () => null)
}
