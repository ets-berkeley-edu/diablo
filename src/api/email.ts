import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function createEmailTemplate(templateType: string, subjectLine: string, message: string) {
  return axios.post(`${getApiBaseUrl()}/api/email/template/create`, {
    templateType,
    subjectLine,
    message
  })
}

export function deleteTemplate(templateId: number) {
  return axios.delete(`${getApiBaseUrl()}/api/email/template/delete/${templateId}`)
    .then(response => response.data)
}

export function getAllEmailTemplates() {
  return axios.get(`${getApiBaseUrl()}/api/email/templates/all`)
    .then(response => response.data)
}

export function getEmailTemplate(templateId: number) {
  return axios.get(`${getApiBaseUrl()}/api/email/template/${templateId}`)
    .then(response => response.data)
}

export function getEmailTemplateCodes() {
  return axios.get(`${getApiBaseUrl()}/api/email/template/codes`)
    .then(response => response.data)
}

export function sendTestEmail(templateId: number) {
  return axios.get(`${getApiBaseUrl()}/api/email/template/test/${templateId}`)
    .then(response => response.data)
}

export function updateEmailTemplate(
    templateId: number,
    templateType: string,
    subjectLine: string,
    message: string
  ) {
  return axios.post(`${getApiBaseUrl()}/api/email/template/update`, {
    templateId,
    templateType,
    subjectLine,
    message
  })
}
