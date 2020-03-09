import axios from 'axios'
import utils from '@/api/api-utils'

export function signUp(
    publishType: string,
    recordingType: string,
    sectionId: string
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/sign_up`, {
      publishType,
      recordingType,
      sectionId
    })
    .then(response => response.data, error => error)
}

export function getSignUpStatus(termId: number, sectionId: number) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/sign_up/status/${termId}/${sectionId}`)
    .then(response => response.data, () => null)
}
