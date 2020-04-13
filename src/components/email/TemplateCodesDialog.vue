<template>
  <div>
    <v-dialog
      v-model="dialog"
      width="500"
    >
      <template v-slot:activator="{ on }">
        <v-btn
          id="btn-email-template-codes"
          color="secondary"
          dark
          text
          v-on="on"
        >
          Template Codes
        </v-btn>
      </template>

      <v-card class="pt-2">
        <v-card-title class="headline" primary-title>
          Template Codes
        </v-card-title>
        <v-card-text>
          <div class="d-flex">
            <div v-for="(column, index) in columns" :key="index" class="pl-3 w-50">
              <div
                v-for="(code, innerIndex) in column"
                :key="innerIndex"
                class="font-weight-medium pb-2 pt-4">
                <code>{{ code }}</code>
              </div>
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            id="btn-close-template-codes-dialog"
            color="primary"
            text
            @click="dialog = false">
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
  import Utils from '@/mixins/Utils'
  import {getEmailTemplateCodes} from '@/api/email'

  export default {
    name: 'TemplateCodesDialog',
    mixins: [Utils],
    data: () => ({
      dialog: false,
      columns: undefined
    }),
    created() {
      getEmailTemplateCodes().then(codes => {
        const chunk = Math.ceil(codes.length / 2)
        this.columns = [
          codes.slice(0, chunk),
          codes.slice(chunk, chunk + codes.length)
        ]
      })
    }
  }
</script>
