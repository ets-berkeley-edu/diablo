<template>
  <div>
    <v-dialog
      v-model="dialog"
      aria-labelledby="template-codes-modal-header"
      persistent
      role="dialog"
      width="500"
    >
      <template #activator="{props: activatorProps}">
        <v-btn
          id="btn-email-template-codes"
          color="secondary"
          variant="text"
          v-bind="activatorProps"
        >
          Template Codes
        </v-btn>
      </template>
      <v-card class="pt-2">
        <v-card-title>
          <h2 id="template-codes-modal-header" class="title">Template Codes</h2>
        </v-card-title>
        <v-card-text>
          <div class="d-flex">
            <div v-for="(column, index) in columns" :key="index" class="pl-3 w-50">
              <div
                v-for="(code, innerIndex) in column"
                :key="innerIndex"
                class="font-weight-medium pb-2 pt-4"
              >
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
            variant="text"
            @click="dialog = false"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {getEmailTemplateCodes} from '@/api/email'

const dialog = ref(false)
const columns = ref()

onMounted(() => {
  getEmailTemplateCodes().then(codes => {
    const chunk = Math.ceil(codes.length / 2)
    columns.value = [
      codes.slice(0, chunk),
      codes.slice(chunk, chunk + codes.length)
    ]
  })
})
</script>
