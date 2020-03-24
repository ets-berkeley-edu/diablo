import axios from 'axios'
import utils from '@/api/api-utils'

export function getAllRooms() {
  return axios
      .get(`${utils.apiBaseUrl()}/api/berkeley/all_rooms`)
      .then(response => response.data, () => null)
}

export function getCapabilityOptions() {
  return axios
      .get(`${utils.apiBaseUrl()}/api/berkeley/capability_options`)
      .then(response => response.data, () => null)
}

export function getRoom(id) {
  return axios
      .get(`${utils.apiBaseUrl()}/api/berkeley/room/${id}`)
      .then(response => response.data, () => null)
}

export function updateRoomCapability(roomId, capability) {
  return axios
      .post(`${utils.apiBaseUrl()}/api/berkeley/update_room_capability`, {
        roomId,
        capability
      })
      .then(response => response.data, () => null)
}
