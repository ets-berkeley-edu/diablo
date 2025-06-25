<template>
  <v-row class="d-flex">
    <v-menu
      :close-on-content-click="false"
      eager
      :model-value="menu"
      scrim
    >
      <template #activator="{props: menuProps}">
        <v-btn id="kaltura-events-export-menu-btn" class="ml-auto" v-bind="menuProps">
          Export to iCal
        </v-btn>
      </template>
      <v-card
        aria-labelledby="kaltura-events-export-header"
        class="overflow-visible"
        min-width="400"
        role="region"
      >
        <v-card-title>
          <h3 id="kaltura-events-export-header">Export Kalura Events to iCal</h3>
          <div class="text-subtitle-1">Download events within the date range as an iCalendar file.</div>
        </v-card-title>
        <v-card-text class="d-flex pt-2">
          <div id="kaltura-events-export-start-container" class="pr-2">
            <label for="kaltura-events-export-start-input">
              Start Date
            </label>
            <AccessibleDateInput
              container-id="kaltura-events-export-start-container"
              :disabled="isExporting"
              :get-value="() => startDate"
              id-prefix="kaltura-events-export-start"
              :set-value="v => startDate = v"
            />
          </div>
          <div class="d-flex align-center text-h4 pt-4 px-2" role="presentation">-</div>
          <div id="kaltura-events-export-end-container" class="pl-2">
            <label for="kaltura-events-export-end-input">
              End Date
            </label>
            <AccessibleDateInput
              container-id="kaltura-events-export-end-container"
              :disabled="isExporting"
              :get-value="() => endDate"
              id-prefix="kaltura-events-export-end"
              :set-value="v => endDate = v"
            />
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <ProgressButton
            id="kaltura-events-export-submit-btn"
            :action="onSubmit"
            :disabled="isExporting || !(startDate && endDate)"
            :in-progress="isExporting"
            :text="isExporting ? 'Downloading' : 'Download'"
          />
        </v-card-actions>
      </v-card>
    </v-menu>
  </v-row>
</template>

<script setup>
import {ref} from 'vue'
import AccessibleDateInput from '@/components/util/AccessibleDateInput'
import ProgressButton from '@/components/util/ProgressButton'
import {downloadKalturaEvents} from '@/api/room'

const props = defineProps({
  room: {
    required: true,
    type: Object
  }
})

const endDate = ref()
const isExporting = ref(false)
const menu = ref(false)
const startDate = ref()

const onSubmit = () => {
  isExporting.value = true
  downloadKalturaEvents(props.room.id, props.room.location, startDate.value, endDate.value).then(() => {
    isExporting.value = false
    menu.value = false
  })
}
</script>
