import axios from 'axios'
import utils from '@/api/api-utils'

export function approve(
    publishType: string,
    recordingType: string,
    sectionId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/approve`, {
      publishType,
      recordingType,
      sectionId
    })
    .then(response => response.data, error => error)
}

export function getApprovals(termId: number, sectionId: number) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/approvals/${termId}/${sectionId}`)
    .then(response => response.data, () => null)
}
