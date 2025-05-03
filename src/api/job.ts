import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function getJobHistory() {
  return axios.get(`${getApiBaseUrl()}/api/job/history`)
}

export function getJobSchedule() {
  return axios.get(`${getApiBaseUrl()}/api/job/schedule`)
}

export function getLastSuccessfulRun(jobKey) {
  return axios.get(`${getApiBaseUrl()}/api/job/${jobKey}/last_successful_run`)
}

export function setJobDisabled(jobId, disable) {
  return axios.post(`${getApiBaseUrl()}/api/job/disable`, {
    jobId,
    disable
  })
}

export function startJob(jobKey) {
  return axios.get(`${getApiBaseUrl()}/api/job/${jobKey}/start`)
}

export function updateJobSchedule(jobId, type, value) {
  return axios.post(`${getApiBaseUrl()}/api/job/schedule/update`, {
    jobId,
    type,
    value
  })
}
