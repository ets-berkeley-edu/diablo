<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start p-3">
      <div class="pt-2">
        <h1><v-icon class="pb-2" large>mdi-candle</v-icon> The Attic</h1>
      </div>
    </v-card-title>
    <div class="ma-3">
      <h2>Diablo Configs</h2>
      <v-data-table
        disable-pagination
        :headers="headers"
        hide-default-footer
        :items="items"
      >
        <template v-slot:body="{ items }">
          <tbody>
            <tr v-for="item in items" :key="item.key">
              <td>
                {{ item.key }}
              </td>
              <td>
                <span v-if="isUrl(item.value)"><a :id="`link-to-${item.key}`" :href="item.value" target="_blank">{{ item.value }} <v-icon small class="pl-1">mdi-open-in-new</v-icon></a></span>
                <span v-if="!isUrl(item.value)">{{ item.value }}</span>
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
    </div>
    <div class="ma-3 pt-3">
      <h2>Admin Users</h2>
      <v-data-table
        disable-pagination
        :headers="[
          {text: 'Name', value: 'name'},
          {text: 'Email', value: 'email'},
          {text: 'UID', value: 'uid'}
        ]"
        hide-default-footer
        :items="adminUsers"
      ></v-data-table>
    </div>
  </v-card>
</template>

<script>
  import axios from 'axios'
  import Context from '@/mixins/Context'
  import Vue from 'vue'
  import {getAdminUsers} from '@/api/user'

  export default {
    name: 'Attic',
    mixins: [Context],
    data: () => ({
      adminUsers: undefined,
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
      ],
      items: undefined
    }),
    mounted() {
      this.$loading()
      this.items = []
      getAdminUsers().then(data => {
        this.adminUsers = data
        axios.get(`${Vue.prototype.$config.apiBaseUrl}/api/version`).then(data => {
          this.$_.each({...data, ...this.$config }, (value, key) => {
            this.push(key, value)
          })
          this.items = this.$_.sortBy(this.items, ['key'])
          this.$ready('Attic')
        })
      })
    },
    methods: {
      isUrl(value) {
        return this.$_.startsWith(value, 'https://')
      },
      push(key, value) {
        if (!this.$_.includes(this.excludeConfigs, key)) {
          if (key === 'build') {
            this.items.push({key: 'buildArtifact', value: value.artifact})
            this.items.push({key: 'gitCommit', value: value.gitCommit && `https://github.com/ets-berkeley-edu/diablo/commit/${value.gitCommit}`})
          } else {
            this.items.push({key, value})
          }
        }
      }
    }
  }
</script>
