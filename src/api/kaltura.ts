import axios from 'axios'
import {getApiBaseUrl} from '@/api/api-utils'

export function getKalturaCategory(courseSiteId) {
  return axios.get(`${getApiBaseUrl()}/api/kaltura/category/canvas/${courseSiteId}`)
}
