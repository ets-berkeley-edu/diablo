import axios from 'axios'
import utils from '@/api/api-utils'

export function createEmailTemplate(templateType, name, subjectLine, message) {
  return axios.post(`${utils.apiBaseUrl()}/api/email_template/create`, {
    templateType,
    name,
    subjectLine,
    message
  })
}

export function getAllEmailTemplates() {
  return axios.get(`${utils.apiBaseUrl()}/api/email_templates/all`)
}

export function getEmailTemplate(templateId) {
  return axios.get(`${utils.apiBaseUrl()}/api/email_template/${templateId}`)
}

export function getEmailTemplateCodes() {
  return axios.get(`${utils.apiBaseUrl()}//api/email_template/codes`)
}

export function sendTestEmail(templateId) {
  return axios.get(`${utils.apiBaseUrl()}/api/email_template/test/${templateId}`)
}

export function updateEmailTemplate(templateId, templateType, name, subjectLine, message) {
  return axios.post(`${utils.apiBaseUrl()}/api/email_template/update`, {
    templateId,
    templateType,
    name,
    subjectLine,
    message
  })
}
