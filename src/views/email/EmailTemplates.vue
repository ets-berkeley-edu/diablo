<template>
  <v-container v-if="!loading" class="pa-0" fluid>
    <v-card outlined class="elevation-1">
      <v-card-title>
        <PageTitle icon="mdi-pencil" text="Email Templates" />
      </v-card-title>
      <v-card-text class="pb-0">
        <div>
          When email is ready to send it is put in a queue. Background jobs add emails to the queue &mdash;
          for example, the Kaltura job queues up 'Recordings scheduled' emails.
          Some email is queued by the application in real-time. For example, the 'Waiting for approval' and
          'Notify instructor of changes' emails are added to the queue when an instructor approves his/her course
          for Course Capture.
        </div>
        <div class="pt-2">
          The Queued Emails job is what actually sends email.
        </div>
      </v-card-text>
      <v-card-title class="pb-0 pt-0">
        <v-spacer class="pb-0 pt-0 w-50"></v-spacer>
        <v-select
          id="select-email-template-type"
          :items="emailTemplateTypes"
          label="Create New Template"
          prepend-icon="mdi-file-document-outline"
          @change="createNewTemplate"
        >
          <span :id="`email-template-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item.text }}</span>
        </v-select>
      </v-card-title>
      <v-card-text>
        <v-data-table
          disable-pagination
          disable-sort
          :headers="headers"
          hide-default-footer
          :items="emailTemplates"
          :loading="refreshing"
          no-results-text="No matching emailTemplates"
        >
          <template v-slot:body="{ items }">
            <tbody>
              <tr v-if="!items.length">
                <td colspan="6" class="pa-6 subtitle-1">
                  You have no email templates. To get started, select a type of template from the "Create New Template" menu above.
                </td>
              </tr>
              <tr v-for="template in items" :key="template.id">
                <td>
                  <router-link :id="`template-${template.id}`" :to="`/email/template/edit/${template.id}`">{{ template.name }}</router-link>
                </td>
                <td :id="`template-${template.typeName}-subject-line`" class="w-50">
                  {{ template.subjectLine }}
                </td>
                <td :id="`template-${template.typeName}-type-name`">
                  {{ template.typeName }}
                </td>
                <td class="text-no-wrap">
                  {{ template.createdAt | moment('MMM DD, YYYY') }}
                </td>
                <td>
                  <v-btn
                    :id="`send-test-email-${template.typeName}`"
                    icon
                    @click="sendTestEmail(template.id)"
                  >
                    <v-icon>mdi-email-outline</v-icon>
                  </v-btn>
                </td>
                <td>
                  <v-btn
                    :id="`delete-email-template-${template.typeName}`"
                    icon
                    @click="deleteEmailTemplate(template.id)"
                  >
                    <v-icon>mdi-trash-can-outline</v-icon>
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
  import Context from '@/mixins/Context'
  import PageTitle from '@/components/util/PageTitle'
  import Utils from '@/mixins/Utils'
  import {deleteTemplate, getAllEmailTemplates, sendTestEmail} from '@/api/email'

  export default {
    name: 'EmailTemplates',
    mixins: [Context, Utils],
    components: {PageTitle},
    data: () => ({
      headers: [
        {text: 'Name', value: 'name'},
        {text: 'Subject Line', value: 'subjectLine'},
        {text: 'Type', value: 'typeName'},
        {text: 'Created', value: 'createdAt'},
        {text: 'Test', class: 'pl-5 pr-0 mr-0'},
        {text: 'Delete', class: 'pl-5 pr-0 mr-0'}
      ],
      emailTemplates: undefined,
      emailTemplateTypes: undefined,
      refreshing: false
    }),
    mounted() {
      this.$loading()
      this.loadAllEmailTemplates().then(() => {
        this.$ready('Email Templates')
      })
    },
    methods: {
      createNewTemplate(type) {
        this.goToPath(`/email/template/create/${type}`)
      },
      deleteEmailTemplate(templateId) {
        this.refreshing = true
        deleteTemplate(templateId).then(() => {
          this.alertScreenReader('Email template deleted.')
          this.loadAllEmailTemplates().then(() => {
            this.refreshing = false
          })
        })
      },
      loadAllEmailTemplates() {
        return getAllEmailTemplates().then(data => {
          this.emailTemplates = data
          this.emailTemplateTypes = []
          const disableTheseTypes = this.$_.map(this.emailTemplates, 'templateType')
          const isDisabled = type => {
            return this.$_.includes(disableTheseTypes, type)
          }
          this.emailTemplateTypes = this.getSelectOptionsFromObject(this.$config.emailTemplateTypes, isDisabled)
        })
      },
      sendTestEmail(templateId) {
        sendTestEmail(templateId).then(() => {
          this.snackbarOpen('Test email sent. Check your inbox.')
        })
      }
    }
  }
</script>
