<template>
  <div>
    <h2>Diablo Configs</h2>
    <v-data-table
      disable-pagination
      :headers="headers"
      hide-default-footer
      :items="configs"
    >
      <template #body="{items}">
        <tbody>
          <tr v-for="config in items" :key="config.key">
            <td>
              {{ config.key }}
            </td>
            <td>
              <span v-if="isUrl(config.value)"><a :id="`link-to-${config.key}`" :href="config.value" target="_blank">{{ config.value }} <v-icon small class="pl-1">mdi-open-in-new</v-icon></a></span>
              <span v-if="!isUrl(config.value)">{{ config.value }}</span>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import axios from 'axios'
import Context from '@/mixins/Context'
import Vue from 'vue'

export default {
  name: 'Configs',
  mixins: [Context],
  data: () => ({
    configs: undefined,
    excludeConfigs: [
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
    ],
    headers: [
      {text: 'Key', value: 'key'},
      {text: 'Value', value: 'value'}
    ]
  }),
  mounted() {
    axios.get(`${Vue.prototype.$config.apiBaseUrl}/api/version`).then(data => {
      this.configs = []
      this.$_.each({...data, ...this.$config }, (value, key) => this.pushConfig(key, value))
      this.configs = this.$_.sortBy(this.configs, ['key'])
      this.$ready('Attic')
    })
  },
  methods: {
    isUrl(value) {
      return this.$_.startsWith(value, 'https://')
    },
    pushConfig(key, value) {
      if (!this.$_.includes(this.excludeConfigs, key)) {
        if (key === 'build') {
          this.configs.push({key: 'buildArtifact', value: value.artifact})
          this.configs.push({key: 'gitCommit', value: value.gitCommit && `https://github.com/ets-berkeley-edu/diablo/commit/${value.gitCommit}`})
        } else {
          this.configs.push({key, value})
        }
      }
    }
  }
}
</script>
