import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function createEmailTemplate(templateType, name, subjectLine, message) {
  return axios.post(`${getApiBaseUrl()}/api/email/template/create`, {
    templateType,
    name,
    subjectLine,
    message
  })
}

export function deleteTemplate(templateId) {
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

export function queueEmail(emailTemplateType, sectionId, termId) {
  return axios.post(`${getApiBaseUrl()}/api/emails/queue`, {
    emailTemplateType,
    sectionId,
    termId
  })
}

export function sendTestEmail(templateId) {
  return axios.get(`${getApiBaseUrl()}/api/email/template/test/${templateId}`)
    .then(response => response.data)
}

export function updateEmailTemplate(templateId, templateType, name, subjectLine, message) {
  return axios.post(`${getApiBaseUrl()}/api/email/template/update`, {
    templateId,
    templateType,
    name,
    subjectLine,
    message
  })
}
