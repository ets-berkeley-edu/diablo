import axios from 'axios'
import utils from '@/api/api-utils'

export function getAllRooms() {
  return axios
      .get(`${utils.apiBaseUrl()}/api/berkeley/all_rooms`)
      .then(response => response.data, () => null)
}

export function getRoom(id) {
  return axios
      .get(`${utils.apiBaseUrl()}/api/berkeley/room/${id}`)
      .then(response => response.data, () => null)
}
