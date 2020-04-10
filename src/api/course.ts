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

export function getApprovals(termId: number, sectionId: number) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/course/approvals/${termId}/${sectionId}`)
}

export function getCourses(filter, termId) {
  return axios.post(`${utils.apiBaseUrl()}/api/courses`, {
    filter,
    termId
  })
}

export function getCourseChanges(termId) {
  return axios.get(`${utils.apiBaseUrl()}/api/courses/changes/${termId}`)
}

export function updateOptOut(termId, sectionId, optOut) {
  return axios.post(`${utils.apiBaseUrl()}/api/course/opt_out/update`, {
    optOut,
    sectionId,
    termId
  })
}
