import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function getJobHistory() {
  return axios.get(`${getApiBaseUrl()}/api/job/history`)
    .then(response => response.data)
}

export function getJobSchedule() {
  return axios.get(`${getApiBaseUrl()}/api/job/schedule`)
    .then(response => response.data)
}

export function getLastSuccessfulRun(jobKey: string) {
  return axios.get(`${getApiBaseUrl()}/api/job/${jobKey}/last_successful_run`)
    .then(response => response.data)
}

export function setJobDisabled(jobId: number, disable: boolean) {
  return axios.post(`${getApiBaseUrl()}/api/job/disable`, {
    jobId,
    disable
  })
    .then(response => response.data)
}

export function startJob(jobKey: string) {
  return axios.get(`${getApiBaseUrl()}/api/job/${jobKey}/start`)
    .then(response => response.data)
}

export function updateJobSchedule(jobId: number, type: string, value: string) {
  return axios.post(`${getApiBaseUrl()}/api/job/schedule/update`, {
    jobId,
    type,
    value
  })
}
