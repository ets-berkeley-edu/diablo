<template>
  <v-row class="d-flex">
    <v-menu
      v-model="menu"
      :close-on-content-click="false"
      eager
      scrim
    >
      <template #activator="{props: menuProps}">
        <v-btn id="kaltura-events-export-menu-btn" class="ml-auto" v-bind="menuProps">
          Export to iCal
        </v-btn>
      </template>
      <v-card
        aria-labelledby="kaltura-events-export-header"
        class="overflow-visible pa-1"
        role="region"
        width="470"
      >
        <v-card-title>
          <h3 id="kaltura-events-export-header">Export Kalura Events to iCal</h3>
          <div class="text-subtitle-1">Download events within the date range as an iCalendar file.</div>
        </v-card-title>
        <v-card-text class="py-2">
          <div class="d-flex">
            <div id="kaltura-events-export-start-container" class="pr-2">
              <label for="kaltura-events-export-start-input">
                Start Date
              </label>
              <AccessibleDateInput
                aria-describedby="kaltura-events-export-error"
                aria-label="Start of date range"
                container-id="kaltura-events-export-start-container"
                :disabled="isExporting"
                :get-value="() => startDate"
                id-prefix="kaltura-events-export-start"
                required
                :set-value="onChangeStartDate"
              />
            </div>
            <div class="d-flex align-center text-h4 pt-4 px-2" role="presentation">-</div>
            <div id="kaltura-events-export-end-container" class="pl-2">
              <label for="kaltura-events-export-end-input">
                End Date
              </label>
              <AccessibleDateInput
                aria-describedby="kaltura-events-export-error"
                aria-label="End of date range"
                container-id="kaltura-events-export-end-container"
                :disabled="isExporting"
                :get-value="() => endDate"
                id-prefix="kaltura-events-export-end"
                required
                :set-value="onChangeEndDate"
              />
            </div>
          </div>
          <div
            id="kaltura-events-export-error"
            aria-live="assertive"
            class="error-container"
            role="alert"
          >
            <v-alert
              v-if="size(error)"
              class="my-2"
              density="compact"
              :icon="false"
              role="none"
              type="error"
              variant="tonal"
            >
              {{ error }}
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <ProgressButton
            id="kaltura-events-export-submit-btn"
            :action="onSubmit"
            :aria-label="`${isExporting ? 'Downloading' : 'Download'} iCalendar events`"
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
import {DateTime} from 'luxon'
import {ref} from 'vue'
import {size} from 'lodash'
import AccessibleDateInput from '@/components/util/AccessibleDateInput'
import ProgressButton from '@/components/util/ProgressButton'
import {downloadKalturaEvents} from '@/api/room'
import {putFocusNextTick} from '@/lib/utils'

const props = defineProps({
  room: {
    required: true,
    type: Object
  }
})

const endDate = ref()
const error = ref('')
const isExporting = ref(false)
const menu = ref(false)
const startDate = ref()

const formatDate = d => {
  return DateTime.fromJSDate(d).toISODate()
}

const onChangeStartDate = v => {
  startDate.value = v
  error.value = ''
}

const onChangeEndDate = v => {
  endDate.value = v
  error.value = ''
}

const onSubmit = () => {
  isExporting.value = true
  error.value = ''

  downloadKalturaEvents(
    props.room.id,
    props.room.location,
    formatDate(startDate.value),
    formatDate(endDate.value)
  )
    .then(() => {
      isExporting.value = false
      endDate.value = null
      startDate.value = null
      if (menu.value) {
        menu.value = false
        putFocusNextTick('kaltura-events-export-menu-btn')
      }
    })
    .catch(message => {
      isExporting.value = false
      error.value = message
      if (menu.value) {
        putFocusNextTick('kaltura-events-export-menu-btn')
      }
    })
}
</script>

<style scoped>
.error-container {
  min-height: 30px;
}
</style>
