<template>
  <v-dialog
    v-model="dialog"
    aria-labelledby="blackout-modal-header"
    persistent
    role="dialog"
    width="400"
    @update:model-value="onToggleDialog"
  >
    <template #activator="{props: activatorProps}">
      <v-btn id="create-blackout-btn" v-bind="activatorProps">
        Create New<span class="sr-only"> Blackout Date</span>
      </v-btn>
    </template>
    <v-card>
      <v-card-title class="pb-1">
        <h2 id="blackout-modal-header" class="title">Create New Blackout</h2>
      </v-card-title>
      <v-card-text>
        <div class="pb-2">
          <v-text-field
            id="input-blackout-name"
            v-model="name"
            aria-label="Blackout name"
            aria-required="true"
            label="Name"
            maxlength="255"
            :rules="[s => !!s || 'Required', s => !includes(existingNames, trim(s).toLowerCase()) || 'Name not available']"
            @keypress.enter="create"
          />
        </div>
        <span id="create-blackout-desc" class="text-body-2">
          To select a date range, click once on the start date and once on end date.
        </span>
        <div class="mt-2 text-center w-100">
          <DatePicker
            v-model="range"
            aria-describedby="create-blackout-desc"
            :attributes="attributes"
            :disabled-dates="disabledDates"
            is-required
            :max-date="today.plus({years: 2}).toJSDate()"
            :min-date="today.toJSDate()"
            :model-modifiers="{range: true, date: true}"
          />
        </div>
      </v-card-text>
      <v-card-actions class="pt-0">
        <v-spacer></v-spacer>
        <div class="pb-3 pr-2">
          <ProgressButton
            id="save-blackout"
            :action="create"
            :disabled="isDisabled"
            :in-progress="isSaving"
            :text="isSaving ? 'Saving' : 'Save'"
          >
          </ProgressButton>
          <v-btn
            id="cancel-edit-of-blackout"
            class="ml-2"
            text
            @click="cancel"
          >
            Cancel
          </v-btn>
        </div>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import {computed, defineModel, defineProps, onMounted, ref} from 'vue'
import {includes, map, trim} from 'lodash'
import {DateTime} from 'luxon'
import ProgressButton from '@/components/util/ProgressButton'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {createBlackout} from '@/api/blackout'

const props = defineProps({
  blackouts: {
    required: true,
    type: Array
  },
  onClose: {
    required: true,
    type: Function
  }
})

const dialog = ref(false)
const isSaving = ref(false)
const name = ref()
const range = defineModel('range', {
  default: {start: undefined, end: undefined},
  type: Date
})
const today = DateTime.now()

const attributes = computed(() => {
  return map(props.blackouts, b => ({
    key: b.name,
    highlight: 'red',
    dates: {
      start: DateTime.fromISO(b.startDate).toJSDate(),
      end: DateTime.fromISO(b.endDate).toJSDate()
    }
  }))
})
const disabledDates = computed(() => {
  return map(props.blackouts, b => ({
    start: DateTime.fromISO(b.startDate).toJSDate(),
    end: DateTime.fromISO(b.endDate).toJSDate()
  }))
})
const existingNames = computed(() => {
  return map(props.blackouts, b => b.name.toLowerCase())
})
const isDisabled = computed(() => {
  const trimmed = trim(name.value)
  return !trimmed || includes(existingNames.value, trimmed.toLowerCase()) || !range.value.start || !range.value.end
})

onMounted(() => reset())

const cancel = () => {
  dialog.value = false
  alertScreenReader('Canceled.')
  props.onClose(false)
  putFocusNextTick('create-blackout-btn')
}

const create = () => {
  if (!isDisabled.value) {
    isSaving.value = true
    const format = date => {
      return DateTime.fromObject(date).toFormat('yyyy-MM-dd')
    }
    createBlackout(name.value, format(range.value.start), format(range.value.end)).then(() => {
      alertScreenReader('Blackout created')
      isSaving.value = false
      dialog.value = false
      props.onClose(true)
      putFocusNextTick('create-blackout-btn')
    })
  }
}

const onToggleDialog = isOpen => {
  reset()
  if (isOpen) {
    putFocusNextTick('input-blackout-name')
  }
}

const reset = () => {
  name.value = null
  range.value = {
    start: undefined,
    end: undefined,
  }
}
</script>
