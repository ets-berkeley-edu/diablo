import axios from 'axios'
import utils from '@/api/api-utils'

export function getTermSummary(termId) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/report/term/${termId}`)
    .then(response => response.data, () => null)
}
