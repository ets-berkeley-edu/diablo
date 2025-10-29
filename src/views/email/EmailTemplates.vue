<template>
  <v-container v-if="!contextStore.loading" class="pa-0" fluid>
    <v-card elevation="0">
      <v-card-title>
        <PageTitle :icon="mdiEmailOpenMultipleOutline" text="Email Templates" />
      </v-card-title>
      <v-card-text class="font-size-16">
        <div>
          When email is ready to send it is put in a queue. Background jobs add emails to the queue &mdash;
          for example, the Kaltura job queues up 'Recordings scheduled' emails.
          Some email is queued by the application in real-time. For example, the 'Waiting for approval' and
          'Notify instructor of changes' emails are added to the queue when an instructor approves his/her course
          for Course Capture.
        </div>
        <div class="mt-3">
          The Queued Emails job is what actually sends email.
        </div>
        <v-row>
          <v-spacer />
          <v-col
            cols="12"
            lg="6"
            md="7"
            sm="8"
          >
            <v-select
              id="select-email-template-type"
              ref="templateTypesSelect"
              :aria-describedby="undefined"
              aria-label="Create New Template"
              autocomplete="off"
              hide-details
              item-props
              :items="emailTemplateTypes"
              label="Create New Template"
              :list-props="{ariaLabel: 'Email template options', ariaLive: 'off', id: 'email-template-type-list'}"
              :menu-props="{attach: menuContainer, eager: true, id: 'email-template-type-menu'}"
              :prepend-icon="mdiFileDocumentOutline"
              return-object
              :title="undefined"
              :value="undefined"
              @update:menu="onToggleTemplateTypesMenu"
              @update:model-value="createNewTemplate"
            >
              <template #item="{props: itemProps, item}">
                <v-list-item
                  :id="`email-template-option-${item.value}`"
                  :aria-disabled="item.props.disabled"
                  :disabled="item.props.disabled"
                  v-bind="itemProps"
                  @keydown.tab.stop.prevent="closeTemplateTypesMenu"
                />
              </template>
            </v-select>
            <div id="email-template-type-menu-container" ref="menuContainer" />
          </v-col>
        </v-row>
        <v-data-table
          :class="{'v-table-padding-override': emailTemplates.length}"
          disable-pagination
          :headers="headers"
          hide-default-footer
          :items="emailTemplates"
          :items-per-page="-1"
          :loading="refreshing"
        >
          <template #headers="{columns}">
            <tr>
              <th
                v-for="(column, colIndex) in columns"
                :id="`email-templates-${column.value}-th`"
                :key="colIndex"
                class="font-size-13 font-weight-bold text-medium-emphasis text-no-wrap"
                :class="column.class"
                scope="col"
              >
                {{ column.title }}
              </th>
            </tr>
          </template>
          <template #body="{items}">
            <tr v-if="!items.length">
              <td class="py-5 text-center text-subtitle-1" :colspan="headers.length">
                You have no email templates. To get started, select a type of template from the "Create New Template" menu above.
              </td>
            </tr>
            <tr v-for="template in items" :key="template.id">
              <td :id="`template-${template.id}-type-name`">
                <router-link
                  :id="`template-${template.id}`"
                  :to="`/email/template/edit/${template.id}`"
                >
                  {{ template.typeName }}<span class="sr-only"> - Edit Template</span>
                </router-link>
              </td>
              <td :id="`template-${template.id}-subject-line`" class="w-50">
                {{ template.subjectLine }}
              </td>
              <td :id="`template-${template.id}-createdAt`" class="text-no-wrap">
                {{ DateTime.fromISO(template.createdAt).toLocaleString(DateTime.DATE_MED) }}
              </td>
              <td class="text-center">
                <v-btn
                  :id="`send-test-email-${template.id}`"
                  :aria-label="`Send test email using template ${template.typeName}`"
                  variant="plain"
                  icon
                  @click="onClickSend(template.id)"
                >
                  <v-icon :icon="mdiEmailOutline" />
                </v-btn>
              </td>
              <td class="text-center">
                <v-btn
                  :id="`delete-email-template-${template.id}`"
                  :aria-label="`Delete ${template.typeName} email template`"
                  variant="plain"
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
import {get, includes, map} from 'lodash'
import {mdiEmailOpenMultipleOutline, mdiEmailOutline, mdiFileDocumentOutline, mdiTrashCanOutline} from '@mdi/js'
import {onMounted, ref, useTemplateRef} from 'vue'
import {useRouter} from 'vue-router'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
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
const emailTemplates = ref([])
const emailTemplateTypes = ref([])
const menuContainer = ref()
const refreshing = ref(false)
const router = useRouter()
const templateTypesSelect = useTemplateRef('templateTypesSelect')

contextStore.loadingStart()

onMounted(() => {
  loadAllEmailTemplates().then(() => {
    contextStore.loadingComplete()
  })
})

const closeTemplateTypesMenu = () => {
  templateTypesSelect.value.menu = false
}

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
    emailTemplateTypes.value = map(contextStore.config.emailTemplateTypes, (title, value) => {
      return {
        disabled: isDisabled(value),
        id: `email-template-type-option-${value}`,
        role: 'option',
        tabindex: 0,
        title: title,
        value: value
      }
    })
  })
}

const onClickSend = templateId => {
  sendTestEmail(templateId).then(() => {
    contextStore.snackbarOpen('Test email sent. Check your inbox.')
    putFocusNextTick('btn-close-alert')
  })
}

const onToggleTemplateTypesMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick(get(emailTemplateTypes, '0.id', 'email-template-type-list'))
  }
}
</script>

<style>
.email-templates-title-th {
  min-width: 12.5rem;
  width: 30%;
}
</style>
