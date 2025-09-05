import _ from 'lodash'
import axios from 'axios'
import fileDownload from 'js-file-download'
import {DateTime} from 'luxon'
import {getApiBaseUrl} from '@/api/api-utils'
import type {OptIn} from '@/lib/types'

export function deleteCourseNote(termId: number, sectionId: number) {
  return axios.post(`${getApiBaseUrl()}/api/course/note/delete`, {
    sectionId,
    termId
  }).then(response => response.data)
}

export function downloadCSV(filter: string, termId: string) {
  const now = DateTime.now().toFormat('yyyy-MM-dd_HH-mm-ss')
  const filename = `courses-${_.snakeCase(filter)}-${termId}_${now}.csv`
  return axios.post(`${getApiBaseUrl()}/api/courses/csv`, {
    filter,
    termId
  }).then(response => fileDownload(response.data, filename), () => null)
}

export function getCourse(termId: number, sectionId: number) {
  return axios.get(`${getApiBaseUrl()}/api/course/${termId}/${sectionId}`)
    .then(response => response.data)
}

export function getCourseSite(siteId: number) {
  return axios.get(`${getApiBaseUrl()}/api/course_site/${siteId}`)
    .then(response => response.data)
}

export function getCourses(filter: string, termId: string) {
  return axios.post(`${getApiBaseUrl()}/api/courses`, {
    filter,
    termId
  }).then(response => response.data)
}

export function getCoursesReport(termId: string) {
  return axios.get(`${getApiBaseUrl()}/api/courses/report/${termId}`)
    .then(response => response.data)
}

export function updateCollaborators(
    collaboratorUids: string[],
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${getApiBaseUrl()}/api/course/collaborator_uids/update`, {
      collaboratorUids,
      sectionId,
      termId
    }).then(response => response.data)
}

export function updateCourseNote(
  termId: number,
  sectionId: number,
  body: string
) {
  return axios.post(`${getApiBaseUrl()}/api/course/note/update`, {
    sectionId,
    termId,
    body
  }).then(response => response.data)
}

export function updateOptIn(
    instructorUid: string,
    termId: string,
    sectionId: number,
    optIn: OptIn
  ) {
  return axios.post(`${getApiBaseUrl()}/api/course/opt_in/update`, {
    instructorUid,
    optIn,
    sectionId,
    termId
  }).then(response => response.data)
}

export function updatePublishType(
    canvasSiteIds: string[],
    publishType: boolean,
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${getApiBaseUrl()}/api/course/publish_type/update`, {
      canvasSiteIds,
      publishType,
      sectionId,
      termId
    }).then(response => response.data)
}

export function updateRecordingType(
    recordingType: boolean,
    sectionId: string,
    termId: string
) {
  return axios
    .post(`${getApiBaseUrl()}/api/course/recording_type/update`, {
      recordingType,
      sectionId,
      termId
    }).then(response => response.data)
}
