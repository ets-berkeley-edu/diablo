import {snakeCase} from 'lodash'
import axios from 'axios'
import fileDownload from 'js-file-download'
import {DateTime} from 'luxon'
import type {OuijaFilter} from '@/stores/ouija'
import {getApiBaseUrl} from '@/api/api-utils'

export function deleteCourseNote(termId: number, sectionId: number) {
  return axios.post(`${getApiBaseUrl()}/api/course/note/delete`, {
    sectionId,
    termId
  }).then(response => response.data)
}

export function downloadCSV(filter: string | OuijaFilter, termId: number) {
  const now = DateTime.now().toFormat('yyyy-MM-dd_HH-mm-ss')
  const filename = `courses-${snakeCase(filter.toString())}-${termId}_${now}.csv`
  return axios.post(`${getApiBaseUrl()}/api/courses/csv`, {
    filter,
    termId
  }).then(response => fileDownload(response.data, filename), () => null)
}

export function getCourse(termId: number | string, sectionId: number | string) {
  return axios.get(`${getApiBaseUrl()}/api/course/${termId}/${sectionId}`)
    .then(response => response.data)
}

export function getCourseSite(siteId: number) {
  return axios.get(`${getApiBaseUrl()}/api/course_site/${siteId}`)
    .then(response => response.data)
}

export function getCourses(filter: string | OuijaFilter, termId: number) {
  return axios.post(`${getApiBaseUrl()}/api/courses`, {
    filter,
    termId
  }).then(response => response.data)
}

export function getCoursesReport(termId: string) {
  return axios.get(`${getApiBaseUrl()}/api/courses/report/${termId}`)
    .then(response => response.data)
}

export function updateCollaborators(sectionId: number, termId: number, uids: string[]) {
  const url = `${getApiBaseUrl()}/api/course/collaborators/update`
  return axios.post(url, {sectionId, termId, uids}).then(response => response.data)
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

export function updatePublishType(canvasSiteIds: string[], publishType: string, sectionId: number, termId: number) {
  const url = `${getApiBaseUrl()}/api/course/publish_type/update`
  return axios.post(url, {canvasSiteIds, publishType, sectionId, termId}).then(response => response.data)
}

export function toggleCourseOptIn(
  optIn: boolean,
  sectionId: number,
  termId: number
) {
  const url = `${getApiBaseUrl()}/api/course/admin/opt_in`
  const params = {
    optIn,
    sectionId,
    termId
  }
  return axios.post(url, params).then(response => response.data)
}

export function toggleInstructorOptIn(
  instructorUid: string,
  optIn: boolean,
  sectionId: number,
  termId: number
) {
  const url = `${getApiBaseUrl()}/api/course/instructor/opt_in`
  const params = {
    instructorUid,
    optIn,
    sectionId,
    termId
  }
  return axios.post(url, params).then(response => response.data)
}
