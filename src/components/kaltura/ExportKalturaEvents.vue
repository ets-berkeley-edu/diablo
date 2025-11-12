<template>
  <v-menu
    v-model="menu"
    :close-on-content-click="false"
    eager
    scrim
    @update:model-value="onUpdateMenuModel"
  >
    <template #activator="{props: menuProps}">
      <v-btn id="kaltura-events-export-menu-btn" color="primary" v-bind="menuProps">
        Export Events to iCal
      </v-btn>
    </template>
    <v-card
      aria-labelledby="kaltura-events-export-header"
      class="overflow-visible pa-4"
      role="region"
      width="470"
    >
      <v-card-title>
        <h3 id="kaltura-events-export-header">Export Kaltura Events to iCal</h3>
        <div class="text-subtitle-1 text-wrap">Download events as an iCalendar file per date range.</div>
      </v-card-title>
      <v-card-text class="py-0">
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
              :max-date="endDate"
              :min-date="currentTermBegin"
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
              :max-date="currentTermEnd"
              :min-date="startDate"
              required
              :set-value="onChangeEndDate"
            />
          </div>
        </div>
        <v-expand-transition
          id="kaltura-events-export-error"
          aria-live="assertive"
          role="alert"
        >
          <v-alert
            v-if="size(error)"
            class="mt-3"
            density="compact"
            :icon="false"
            role="none"
            type="error"
            variant="tonal"
          >
            {{ error }}
          </v-alert>
        </v-expand-transition>
      </v-card-text>
      <v-card-actions class="mt-3 px-4 pb-4 pt-0">
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
</template>

<script lang="ts" setup>
import type {PropType} from 'vue'
import {DateTime} from 'luxon'
import {onMounted, ref} from 'vue'
import {size} from 'lodash'
import AccessibleDateInput from '@/components/util/AccessibleDateInput.vue'
import ProgressButton from '@/components/util/ProgressButton.vue'
import type {Room} from '@/lib/types'
import {downloadKalturaEvents} from '@/api/room'
import {putFocusNextTick} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

const props = defineProps({
  room: {
    default: () => undefined,
    required: false,
    type: Object as PropType<Room>
  }
})

const contextStore = useContextStore()
const currentTermBegin = ref()
const currentTermEnd = ref()
const endDate = ref()
const error = ref('')
const isExporting = ref(false)
const menu = ref(false)
const startDate = ref()

onMounted(() => {
  currentTermBegin.value = DateTime.fromISO(contextStore.config.currentTermBegin).toJSDate()
  currentTermEnd.value = DateTime.fromISO(contextStore.config.currentTermEnd).toJSDate()
})

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
    props.room,
    formatDate(startDate.value),
    formatDate(endDate.value)
  )
    .then(() => {
      isExporting.value = false
      endDate.value = undefined
      startDate.value = undefined
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
      } else {
        contextStore.snackbarReportError(error.value)
      }
    })
}

const onUpdateMenuModel = (value: boolean) => {
  if (!value) {
    endDate.value = undefined
    startDate.value = undefined
    error.value = ''
  }
}
</script>
