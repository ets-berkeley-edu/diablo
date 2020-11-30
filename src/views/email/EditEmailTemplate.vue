<template>
  <v-form>
    <v-container v-if="!loading" fluid>
      <v-row class="align-start d-flex justify-space-between pb-2" no-gutters>
        <PageTitle icon="mdi-email-edit-outline" :text="pageTitle" />
        <h2 class="pt-4 title">
          <span class="font-weight-bold">Type:</span>&nbsp;&nbsp;
          <span id="template-type-name" class="font-italic">{{ typeName }}</span>
        </h2>
      </v-row>
      <v-row class="pl-4">
        <v-col cols="8">
          <v-text-field
            id="input-template-name"
            v-model="name"
            aria-required="true"
            label="Template Name"
            maxlength="255"
            :rules="[s => !!s || 'Required']"
          >
          </v-text-field>
        </v-col>
        <v-spacer></v-spacer>
      </v-row>
      <v-row class="pl-4">
        <v-col cols="8">
          <v-text-field
            id="input-template-subject-line"
            v-model="subjectLine"
            aria-required="true"
            label="Subject"
            maxlength="255"
            :rules="[s => !!s || 'Required']"
          >
          </v-text-field>
        </v-col>
        <v-spacer></v-spacer>
      </v-row>
      <v-row class="mt-4">
        <v-col>
          <TiptapVuetify
            id="textarea-template-body"
            v-model="message"
            :extensions="extensions"
            placeholder="Message"
            :toolbar-attributes="{color: 'secondary'}"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="9">
          <TemplateCodesDialog />
        </v-col>
        <v-col cols="3">
          <div class="d-flex">
            <v-btn
              id="save-email-template"
              color="primary"
              :disabled="disableSave"
              @click="createTemplate"
            >
              {{ templateId ? 'Save' : 'Create' }}
            </v-btn>
            <v-btn
              id="cancel-edit-of-email-template"
              text
              color="accent"
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

<script>
  import Context from '@/mixins/Context'
  import PageTitle from '@/components/util/PageTitle'
  import TemplateCodesDialog from '@/components/email/TemplateCodesDialog'
  import Utils from '@/mixins/Utils'
  import { TiptapVuetify, Heading, Bold, Italic, Strike, Underline, Code, Paragraph, BulletList, OrderedList, ListItem, Link, Blockquote, HardBreak, HorizontalRule, History } from 'tiptap-vuetify'
  import {createEmailTemplate, getEmailTemplate, updateEmailTemplate} from '@/api/email'

  export default {
    name: 'CreateEmailTemplate',
    components: {PageTitle, TemplateCodesDialog, TiptapVuetify},
    mixins: [Context, Utils],
    data: () => ({
      extensions: [
        History,
        Blockquote,
        Link,
        Underline,
        Strike,
        Italic,
        ListItem,
        BulletList,
        OrderedList,
        [Heading, {
          options: {
            levels: [1, 2, 3]
          }
        }],
        Bold,
        Code,
        HorizontalRule,
        Paragraph,
        HardBreak
      ],
      latest: false,
      message: undefined,
      name: undefined,
      pageTitle: undefined,
      subjectLine: undefined,
      templateId: undefined,
      templateType: undefined,
      typeName: undefined
    }),
    computed: {
      disableSave() {
        return !this.$_.trim(this.subjectLine) || !this.$_.trim(this.name) || !this.stripHtmlAndTrim(this.message)
      }
    },
    created() {
      this.$loading()
      this.templateType = this.$_.get(this.$route, 'params.type')
      this.typeName = this.$_.get(this.$config.emailTemplateTypes, this.templateType)
      this.templateId = this.$_.get(this.$route, 'params.id')
      this.pageTitle = `${this.templateId ? 'Edit' : 'Create'} Email Template`
      if (this.typeName) {
        this.$ready(`${this.pageTitle} '${this.typeName}'`)
      } else {
        getEmailTemplate(this.templateId).then(data => {
          this.name = data.name
          this.subjectLine = data.subjectLine
          this.message = data.message
          this.templateType = data.templateType
          this.typeName = this.$_.get(this.$config.emailTemplateTypes, data.templateType)
          this.$ready(`${this.pageTitle} '${this.typeName}'`)
        })
      }
    },
    methods: {
      cancel() {
        this.alertScreenReader('Cancelled.')
        this.$router.push({ path: '/email/templates' })
      },
      createTemplate() {
        const done = action => {
          this.alertScreenReader(`Email template '${this.templateType}' ${action}.`)
          this.$router.push({ path: '/email/templates' })
        }
        if (this.disableSave) {
          this.reportError('You must complete the required form fields.')
        } else if (this.templateId) {
          updateEmailTemplate(this.templateId, this.templateType, this.name, this.subjectLine, this.message).then(() => done('updated'))
        } else {
          createEmailTemplate(this.templateType, this.name, this.subjectLine, this.message).then(() => done('created'))
        }
      }
    }
  }
</script>
