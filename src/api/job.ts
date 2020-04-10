import axios from 'axios'
import utils from '@/api/api-utils'

export function getAvailableJobs() {
  return axios.get(`${utils.apiBaseUrl()}/api/jobs/available`)
}

export function startJob(jobId) {
  return axios.get(`${utils.apiBaseUrl()}/api/job/${jobId}/start`)
}
