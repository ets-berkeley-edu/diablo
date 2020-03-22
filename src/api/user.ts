import axios from 'axios'
import utils from '@/api/api-utils'

export function getUser(uid) {
  return axios
      .get(`${utils.apiBaseUrl()}/api/user/${uid}`)
      .then(response => response.data, () => null)
}
