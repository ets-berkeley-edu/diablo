<template>
  <v-container v-if="!loading" class="pa-0" fluid>
    <h2><v-icon class="pb-3" large>mdi-pencil</v-icon> Email Templates</h2>
    <v-card outlined class="elevation-1">
      <v-card-title>
        <v-spacer class="w-50"></v-spacer>
        <v-select
          :items="emailTemplateTypes"
          label="Create New Template"
          prepend-icon="mdi-file-document-outline"
          @change="createNewTemplate"
        ></v-select>
      </v-card-title>
      <v-data-table
        :headers="headers"
        hide-default-footer
        :items="emailTemplates"
        no-results-text="No matching emailTemplates"
        :options="options"
        :page.sync="options.page"
        @page-count="pageCount = $event"
      >
        <template v-slot:body="{ items }">
          <tbody>
            <tr v-if="!items.length">
              <td>
                No Templates found.
              </td>
            </tr>
            <tr v-for="template in items" :key="template.id">
              <td>
                <router-link :id="`template-${template.id}`" :to="`/email/template/edit/${template.id}`">{{ template.name }}</router-link>
              </td>
              <td class="w-50">
                {{ template.subjectLine }}
              </td>
              <td>
                {{ template.typeName }}
              </td>
              <td class="text-no-wrap">
                {{ template.createdAt | moment('MMM DD, YYYY') }}
              </td>
              <td>
                <v-btn
                  icon
                  @click="sendTestEmail(template.id)">
                  <v-icon>mdi-email</v-icon>
                </v-btn>
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
      <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
        <v-pagination
          id="emailTemplates-pagination"
          v-model="options.page"
          :length="pageCount"
          total-visible="10"></v-pagination>
      </div>
    </v-card>
  </v-container>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getAllEmailTemplates, sendTestEmail} from '@/api/email-template'

  export default {
    name: 'EmailTemplates',
    mixins: [Context, Utils],
    data: () => ({
      alert: undefined,
      headers: [
        {text: 'Name', value: 'name'},
        {text: 'Subject Line', value: 'subjectLine'},
        {text: 'Type', value: 'typeName'},
        {text: 'Created', value: 'createdAt'},
        {text: 'Test', sortable: false, class: 'pl-5 pr-0 mr-0'}
      ],
      emailTemplates: undefined,
      emailTemplateTypes: undefined,
      options: {
        page: 1,
        itemsPerPage: 10
      },
      pageCount: undefined
    }),
    mounted() {
      this.$loading()
      getAllEmailTemplates().then(data => {
        this.emailTemplates = data
        this.emailTemplateTypes = this.getSelectOptionsFromObject(this.$config.emailTemplateTypes)
        this.$ready()
      }).catch(this.$ready)
    },
    methods: {
      createNewTemplate(type) {
        this.goToPath(`/email/template/create/${type}`)
      },
      sendTestEmail(templateId) {
        sendTestEmail(templateId).then(() => {
          this.alert = 'Email sent'
        })
      }
    }
  }
</script>
