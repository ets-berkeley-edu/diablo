import _ from 'lodash'
import axios from 'axios'
import moment from 'moment-timezone'
import utils from '@/api/api-utils'

export function approve(
    publishType: string,
    recordingType: string,
    sectionId: string,
    instructorProxies?: any[]
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/approve`, {
      instructorProxies,
      publishType,
      recordingType,
      sectionId
    })
}

export function downloadCSV(filter, termId) {
  const fileDownload = require('js-file-download')
  const now = moment().format('YYYY-MM-DD_HH-mm-ss')
  const filename = `courses-${_.snakeCase(filter)}-${termId}_${now}.csv`
  return axios.post(`${utils.apiBaseUrl()}/api/courses/csv`, {
    filter,
    termId
  }).then(response => fileDownload(response.data, filename), () => null)
}

export function getCourse(termId: number, sectionId: number) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/course/${termId}/${sectionId}`)
}

export function getCourses(filter, termId) {
  return axios.post(`${utils.apiBaseUrl()}/api/courses`, {
    filter,
    termId
  })
}

export function updateCanAprxInstructorsEditRecordings(
    canAprxInstructorsEditRecordings: boolean,
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/can_aprx_instructors_edit_recordings`, {
      canAprxInstructorsEditRecordings,
      sectionId,
      termId
    })
}

export function unschedule(
    termId: string,
    sectionId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/unschedule`, {
      termId,
      sectionId
    })
}

export function getCoursesReport(termId) {
  return axios.get(`${utils.apiBaseUrl()}/api/courses/report/${termId}`)
}

export function updateOptOut(termId, sectionId, optOut) {
  return axios.post(`${utils.apiBaseUrl()}/api/course/opt_out/update`, {
    optOut,
    sectionId,
    termId
  })
}
