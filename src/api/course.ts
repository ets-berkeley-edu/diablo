import _ from 'lodash'
import axios from 'axios'
import moment from 'moment-timezone'
import utils from '@/api/api-utils'

export function deleteCourseNote(termId: number, sectionId: number) {
  return axios.post(`${utils.apiBaseUrl()}/api/course/note/delete`, {
    sectionId,
    termId
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
  return axios.get(`${utils.apiBaseUrl()}/api/course/${termId}/${sectionId}`)
}

export function getCourseSite(siteId: number) {
  return axios.get(`${utils.apiBaseUrl()}/api/course_site/${siteId}`)
}

export function getCourses(filter, termId) {
  return axios.post(`${utils.apiBaseUrl()}/api/courses`, {
    filter,
    termId
  })
}

export function getCoursesReport(termId) {
  return axios.get(`${utils.apiBaseUrl()}/api/courses/report/${termId}`)
}

export function updateCollaborators(
    collaboratorUids: string[],
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/collaborator_uids/update`, {
      collaboratorUids,
      sectionId,
      termId
    })
}

export function updateCourseNote(
  termId: number,
  sectionId: number,
  body: string
) {
  return axios.post(`${utils.apiBaseUrl()}/api/course/note/update`, {
    sectionId,
    termId,
    body
  })
}

export function updateOptOut(instructorUid, termId, sectionId, optOut) {
  return axios.post(`${utils.apiBaseUrl()}/api/course/opt_out/update`, {
    instructorUid,
    optOut,
    sectionId,
    termId
  })
}

export function updatePublishType(
    canvasSiteIds: string[],
    publishType: boolean,
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/publish_type/update`, {
      canvasSiteIds,
      publishType,
      sectionId,
      termId
    })
}

export function updateRecordingType(
    recordingType: boolean,
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/course/recording_type/update`, {
      recordingType,
      sectionId,
      termId
    })
}
