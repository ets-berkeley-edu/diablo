<template>
  <div>
    <h2>Diablo Configs</h2>
    <v-data-table
      caption="Diablo Configs"
      disable-pagination
      :headers="headers"
      hide-default-footer
      :items="configs"
    >
      <template #body="{ items }">
        <tbody>
          <tr v-for="config in items" :key="config.key">
            <td>{{ config.key }}</td>
            <td>
              <template v-if="isUrl(config.value)">
                <a
                  :id="`link-to-${config.key}`"
                  :href="config.value"
                  target="_blank"
                >
                  {{ config.value }}
                  <v-icon small class="pl-1">mdi-open-in-new</v-icon>
                </a>
              </template>
              <template v-else>
                {{ config.value }}
              </template>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import axios from 'axios'
import _ from 'lodash'
import {getApiBaseUrl} from '@/api/api-utils'
import {useContextStore} from '@/stores/context'

interface ConfigItem {
  key: string
  value: any
}

const store = useContextStore()

const configs = ref<ConfigItem[]>([])
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
  'timezone',
]
const headers = [
  {text: 'Key', value: 'key'},
  {text: 'Value', value: 'value'},
]

function isUrl(val: any): val is string {
  return typeof val === 'string' && _.startsWith(val, 'https://')
}

function pushConfig(key: string, value: any) {
  if (excludeConfigs.includes(key)) return

  if (key === 'build' && value && typeof value === 'object') {
    configs.value.push({
      key: 'buildArtifact',
      value: value.artifact,
    })
    if (value.gitCommit) {
      configs.value.push({
        key: 'gitCommit',
        value: `https://github.com/ets-berkeley-edu/diablo/commit/${value.gitCommit}`,
      })
    }
  } else {
    configs.value.push({ key, value })
  }
}

onMounted(async () => {
  // Use the stores’stores config.apiBaseUrl if set, otherwise fallback to utils
  const baseUrl =
    store.config?.apiBaseUrl ?? getApiBaseUrl()

  try {
    const response = await axios.get(`${baseUrl}/api/version`)
    const data = response.data

    configs.value = []
    // merge remote version info + local config
    _.forEach({ ...data, ...store.config }, (value, key) => {
      pushConfig(key, value)
    })
    configs.value = _.sortBy(configs.value, 'key')

    // if you had a “ready” indicator in the old mixin, call it here:
    // stores.ready?.('Diablo Configs')
  } catch (err) {
    console.error('Failed to load configs:', err)
  }
})
</script>
