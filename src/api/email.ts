import axios from 'axios'
import utils from '@/api/api-utils'

export function createEmailTemplate(templateType, name, subjectLine, message) {
  return axios.post(`${utils.apiBaseUrl()}/api/email/template/create`, {
    templateType,
    name,
    subjectLine,
    message
  })
}

export function deleteTemplate(templateId) {
  return axios.delete(`${utils.apiBaseUrl()}/api/email/template/delete/${templateId}`)
}

export function getAllEmailTemplates() {
  return axios.get(`${utils.apiBaseUrl()}/api/email/templates/all`)
}

export function getEmailTemplate(templateId: number) {
  return axios.get(`${utils.apiBaseUrl()}/api/email/template/${templateId}`)
}

export function getEmailTemplateCodes() {
  return axios.get(`${utils.apiBaseUrl()}/api/email/template/codes`)
}

export function queueEmail(emailTemplateType, sectionId, termId) {
  return axios.post(`${utils.apiBaseUrl()}/api/emails/queue`, {
    emailTemplateType,
    sectionId,
    termId
  })
}

export function sendTestEmail(templateId) {
  return axios.get(`${utils.apiBaseUrl()}/api/email/template/test/${templateId}`)
}

export function updateEmailTemplate(templateId, templateType, name, subjectLine, message) {
  return axios.post(`${utils.apiBaseUrl()}/api/email/template/update`, {
    templateId,
    templateType,
    name,
    subjectLine,
    message
  })
}
