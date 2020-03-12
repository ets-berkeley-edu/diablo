import axios from 'axios'
import utils from '@/api/api-utils'

export function getCaptureEnabledRooms() {
  return axios
    .get(`${utils.apiBaseUrl()}/api/salesforce/enabled_rooms`)
    .then(response => response.data, () => null)
}
