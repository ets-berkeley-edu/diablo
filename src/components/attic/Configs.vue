<template>
  <div>
    <h2>Diablo Configs</h2>
    <v-data-table
      disable-pagination
      :headers="headers"
      hide-default-footer
      :items="configs"
      :items-per-page="-1"
    >
      <template #body="{items}">
        <tr v-for="config in items" :key="config.key">
          <td>
            {{ config.key }}
          </td>
          <td>
            <a
              v-if="isUrl(config.value)"
              :id="`link-to-${config.key}`"
              :href="config.value"
              target="_blank"
            >
              {{ config.value }}
              <span class="sr-only">(opens in new tab)</span>
              <v-icon class="pl-1" :icon="mdiOpenInNew" size="small" />
            </a>
            <span v-if="!isUrl(config.value)">{{ config.value }}</span>
          </td>
        </tr>
      </template>
    </v-data-table>
  </div>
</template>

<script setup>
import axios from 'axios'
import {each, includes, sortBy, startsWith} from 'lodash'
import {mdiOpenInNew} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {getApiBaseUrl} from '@/api/api-utils'
import {useContextStore} from '@/stores/context'


const configs = ref([])
const contextStore = useContextStore()
const excludeConfigs = [
  'apiBaseUrl',
  'courseCaptureExplainedUrl',
  'courseCapturePoliciesUrl',
  'currentTermName',
  'devAuthEnabled',
  'emailTemplateTypes',
  'isVueAppDebugMode',
  'publishTypeOptions',
  'roomCapabilityOptions',
  'searchFilterOptions',
  'searchItemsPerPage',
  'timezone'
]
const headers = [
  {title: 'Key', value: 'key'},
  {title: 'Value', value: 'value'}
]

onMounted(() => {
  axios.get(`${getApiBaseUrl()}/api/version`).then(response => {
    each({...response.data, ...contextStore.config}, (value, key) => pushConfig(key, value))
    configs.value = sortBy(configs.value, ['key'])
  })
})

const isUrl = value => {
  return startsWith(value, 'https://')
}

const pushConfig = (key, value) => {
  if (!includes(excludeConfigs, key)) {
    if (key === 'build' && value) {
      configs.value.push({key: 'buildArtifact', value: value.artifact})
      configs.value.push({key: 'gitCommit', value: value.gitCommit && `https://github.com/ets-berkeley-edu/diablo/commit/${value.gitCommit}`})
    } else {
      configs.value.push({key, value})
    }
  }
}
</script>
