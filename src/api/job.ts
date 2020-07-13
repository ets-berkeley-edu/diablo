import axios from 'axios'
import utils from '@/api/api-utils'

export function getJobHistory() {
  return axios.get(`${utils.apiBaseUrl()}/api/job/history`)
}

export function getJobSchedule() {
  return axios.get(`${utils.apiBaseUrl()}/api/job/schedule`)
}

export function getLastSuccessfulRun(jobKey) {
  return axios.get(`${utils.apiBaseUrl()}/api/job/${jobKey}/last_successful_run`)
}

export function setJobDisabled(jobId, disable) {
  return axios.post(`${utils.apiBaseUrl()}/api/job/disable`, {
    jobId,
    disable
  })
}

export function startJob(jobKey) {
  return axios.get(`${utils.apiBaseUrl()}/api/job/${jobKey}/start`)
}

export function updateJobSchedule(jobId, type, value) {
  return axios.post(`${utils.apiBaseUrl()}/api/job/schedule/update`, {
    jobId,
    type,
    value
  })
}
