<template>
  <v-container v-if="!contextStore.loading" class="pa-0" fluid>
    <v-card class="border-sm">
      <v-card-title>
        <PageTitle :icon="mdiEmailOpenMultipleOutline" text="Email Templates" />
      </v-card-title>
      <v-card-text class="text-body-2">
        <div>
          When email is ready to send it is put in a queue. Background jobs add emails to the queue &mdash;
          for example, the Kaltura job queues up 'Recordings scheduled' emails.
          Some email is queued by the application in real-time. For example, the 'Waiting for approval' and
          'Notify instructor of changes' emails are added to the queue when an instructor approves his/her course
          for Course Capture.
        </div>
        <div class="py-2">
          The Queued Emails job is what actually sends email.
        </div>
        <v-row>
          <v-spacer></v-spacer>
          <v-col
            cols="12"
            lg="6"
            md="7"
            sm="8"
          >
            <v-select
              id="select-email-template-type"
              :item-props="true"
              :items="emailTemplateTypes"
              label="Create New Template"
              :list-props="{ariaLabel: 'Email template options', id: 'email-template-type-list'}"
              :menu-props="{attach: menuContainer, eager: true, id: 'email-template-type-menu'}"
              :prepend-icon="mdiFileDocumentOutline"
              return-object
              @update:model-value="createNewTemplate"
            >
              <template #item="{props: itemProps, item}">
                <v-list-item
                  :id="`email-template-option-${item.value}`"
                  :aria-disabled="item.props.disabled"
                  :disabled="item.props.disabled"
                  v-bind="itemProps"
                />
              </template>
            </v-select>
            <div id="email-template-type-menu-container" ref="menuContainer"></div>
          </v-col>
        </v-row>
        <v-data-table
          caption="Email templates"
          class="v-table-padding-override"
          disable-pagination
          :headers="headers"
          hide-default-footer
          :items="emailTemplates"
          :items-per-page="-1"
          :loading="refreshing"
          no-results-text="No matching email templates"
        >
          <template #headers="{columns}">
            <tr>
              <th
                v-for="(column, colIndex) in columns"
                :id="`email-templates-${column.value}-th`"
                :key="colIndex"
                class="font-size-12 font-weight-bold text-medium-emphasis text-no-wrap"
                :class="column.class"
                scope="col"
              >
                {{ column.title }}
              </th>
            </tr>
          </template>
          <template #body="{items}">
            <tr v-if="!items.length">
              <td colspan="6" class="pt-4 text-subtitle-1">
                You have no email templates. To get started, select a type of template from the "Create New Template" menu above.
              </td>
            </tr>
            <tr v-for="template in items" :key="template.id">
              <td :id="`template-${template.id}-type-name`">
                <router-link
                  :id="`template-${template.id}`"
                  :to="`/email/template/edit/${template.id}`"
                >
                  {{ template.typeName }}
                </router-link>
              </td>
              <td :id="`template-${template.id}-subject-line`" class="w-50">
                {{ template.subjectLine }}
              </td>
              <td :id="`template-${template.id}-createdAt`" class="text-no-wrap">
                {{ DateTime.fromISO(template.createdAt).toLocaleString(DateTime.DATE_MED) }}
              </td>
              <td>
                <v-btn
                  :id="`send-test-email-${template.id}`"
                  :aria-label="`Send test email using template ${template.typeName}`"
                  icon
                  @click="onClickSend(template.id)"
                >
                  <v-icon :icon="mdiEmailOutline" />
                </v-btn>
              </td>
              <td>
                <v-btn
                  :id="`delete-email-template-${template.id}`"
                  :aria-label="`Delete ${template.typeName} email template`"
                  icon
                  @click="deleteEmailTemplate(template.id)"
                >
                  <v-icon :icon="mdiTrashCanOutline" />
                </v-btn>
              </td>
            </tr>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import {DateTime} from 'luxon'
import {includes, map} from 'lodash'
import {mdiEmailOpenMultipleOutline, mdiEmailOutline, mdiFileDocumentOutline, mdiTrashCanOutline} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {alertScreenReader, getSelectOptionsFromObject, putFocusNextTick} from '@/lib/utils'
import PageTitle from '@/components/util/PageTitle'
import {deleteTemplate, getAllEmailTemplates, sendTestEmail} from '@/api/email'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const headers = [
  {title: 'Type', value: 'typeName', class: 'email-templates-title-th'},
  {title: 'Subject Line', value: 'subjectLine'},
  {title: 'Created', value: 'createdAt'},
  {title: 'Test', value: 'test', class: 'text-center'},
  {title: 'Delete', value: 'delete', class: 'text-center'}
]
const emailTemplates = ref()
const emailTemplateTypes = ref()
const menuContainer = ref()
const refreshing = ref(false)
const router = useRouter()

onMounted(() => {
  contextStore.loadingStart()
  loadAllEmailTemplates().then(() => {
    contextStore.loadingComplete()
  })
})

const createNewTemplate = option => {
  if (!option.disabled) {
    router.push(`/email/template/create/${option.value}`)
  }
}

const deleteEmailTemplate = templateId => {
  refreshing.value = true
  deleteTemplate(templateId).then(() => {
    alertScreenReader('Email template deleted.')
    loadAllEmailTemplates().then(() => {
      refreshing.value = false
    })
  })
}

const loadAllEmailTemplates = () => {
  return getAllEmailTemplates().then(data => {
    emailTemplates.value = data
    emailTemplateTypes.value = []
    const disableTheseTypes = map(emailTemplates.value, 'templateType')
    const isDisabled = type => {
      return includes(disableTheseTypes, type)
    }
    emailTemplateTypes.value = getSelectOptionsFromObject(contextStore.config.emailTemplateTypes, isDisabled)
  })
}

const onClickSend = templateId => {
  sendTestEmail(templateId).then(() => {
    contextStore.snackbarOpen('Test email sent. Check your inbox.')
    putFocusNextTick('btn-close-alert')
  })
}
</script>

<style>
.email-templates-title-th {
  min-width: 12.5rem;
  width: 30%;
}
</style>
