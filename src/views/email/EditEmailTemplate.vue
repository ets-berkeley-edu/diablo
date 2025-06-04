<template>
  <v-form>
    <v-container v-if="!contextStore.loading" fluid>
      <v-row class="align-start d-flex justify-space-between pb-2" no-gutters>
        <PageTitle :icon="mdiEmailEditOutline" :text="pageTitle" />
        <h2 class="pt-6">
          <span class="font-weight-bold">Type:</span>&nbsp;&nbsp;
          <span id="template-type-name" class="font-italic">{{ typeName }}</span>
        </h2>
      </v-row>
      <v-row class="pl-4">
        <v-col cols="12" sm="8">
          <v-text-field
            id="input-template-subject-line"
            v-model="subjectLine"
            aria-required="true"
            label="Subject"
            maxlength="255"
            :rules="[s => !!s || 'Required']"
          />
        </v-col>
        <v-spacer />
      </v-row>
      <v-row class="mt-4">
        <v-col>
          <RichTextEditor
            id-prefix="template-body"
            :model-value="message"
            placeholder="Message"
            @update:model-value="v => (message = v)"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="6">
          <TemplateCodesDialog />
        </v-col>
        <v-col cols="6">
          <div class="d-flex justify-end">
            <v-btn
              id="save-email-template"
              class="mr-2"
              color="primary"
              :disabled="disableSave"
              @click="createTemplate"
            >
              {{ templateId ? 'Save' : 'Create' }}
            </v-btn>
            <v-btn
              id="cancel-edit-of-email-template"
              variant="text"
              @click="cancel"
            >
              Cancel
            </v-btn>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </v-form>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {get, trim} from 'lodash'
import {mdiEmailEditOutline} from '@mdi/js'
import {useRoute, useRouter} from 'vue-router'
import {alertScreenReader, stripHtmlAndTrim} from '@/lib/utils'
import PageTitle from '@/components/util/PageTitle'
import RichTextEditor from '@/components/util/RichTextEditor'
import TemplateCodesDialog from '@/components/email/TemplateCodesDialog'
import {createEmailTemplate, getEmailTemplate, updateEmailTemplate} from '@/api/email'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const message = ref('')
const pageTitle = ref('')
const route = useRoute()
const router = useRouter()
const subjectLine = ref()
const templateId = ref()
const templateType = ref()
const typeName = ref()

const disableSave = computed(() => {
  return !trim(subjectLine.value) || !stripHtmlAndTrim(message.value)
})

onMounted(() => {
  contextStore.loadingStart()
  templateType.value = get(route, 'params.type')
  typeName.value = get(contextStore.config.emailTemplateTypes, templateType.value)
  templateId.value = get(route, 'params.id')
  pageTitle.value = `${templateId.value ? 'Edit' : 'Create'} Email Template`
  if (typeName.value) {
    contextStore.loadingComplete(`${pageTitle.value} '${typeName.value}'`)
  } else {
    getEmailTemplate(templateId.value).then(data => {
      subjectLine.value = data.subjectLine
      message.value = data.message
      templateType.value = data.templateType
      typeName.value = get(contextStore.config.emailTemplateTypes, data.templateType)
      contextStore.loadingComplete(`${pageTitle.value} '${typeName.value}'`)
    })
  }
})

const cancel = () => {
  alertScreenReader('Cancelled.')
  router.push({path: '/email/templates'})
}

const createTemplate = () => {
  const done = action => {
    alertScreenReader(`Email template '${templateType.value}' ${action}.`)
    router.push({path: '/email/templates'})
  }
  if (disableSave.value) {
    contextStore.snackbarReportError('You must complete the required form fields.')
  } else if (templateId.value) {
    updateEmailTemplate(templateId.value, templateType.value, subjectLine.value, message.value).then(() => done('updated'))
  } else {
    createEmailTemplate(templateType.value, subjectLine.value, message.value).then(() => done('created'))
  }
}
</script>
