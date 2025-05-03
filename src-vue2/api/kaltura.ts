import axios from 'axios'
import utils from '@/api/api-utils'

export function getKalturaCategory(courseSiteId) {
  return axios.get(`${utils.apiBaseUrl()}/api/kaltura/category/canvas/${courseSiteId}`)
}
