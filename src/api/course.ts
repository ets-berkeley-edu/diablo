import axios from 'axios'
import utils from '@/api/api-utils'

export function approve(
    publishType: string,
    recordingType: string,
    sectionId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/approve`, {
      publishType,
      recordingType,
      sectionId
    })
}

export function getAllApprovals(termId) {
  return axios.get(`${utils.apiBaseUrl()}/api/courses/approvals/${termId}`)
}

export function getApprovals(termId: number, sectionId: number) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/course/approvals/${termId}/${sectionId}`)
}

export function getTermSummary(termId) {
  return axios.get(`${utils.apiBaseUrl()}/api/courses/term/${termId}`)
}