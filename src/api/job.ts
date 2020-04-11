import axios from 'axios'
import utils from '@/api/api-utils'

export function getAvailableJobs() {
  return axios.get(`${utils.apiBaseUrl()}/api/jobs/available`)
}

export function getJobHistory(daysCount) {
  return axios.get(`${utils.apiBaseUrl()}/api/job/history/${daysCount}`)
}

export function startJob(jobKey) {
  return axios.get(`${utils.apiBaseUrl()}/api/job/${jobKey}/start`)
}
