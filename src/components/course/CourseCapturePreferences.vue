<template>
  <div>
    <v-expand-transition>
      <v-alert
        v-if="error"
        class="my-1"
        density="compact"
        :icon="false"
        role="none"
        :text="error"
        type="error"
        variant="tonal"
      />
    </v-expand-transition>

    <section aria-labelledby="future-courses-header">
      <h3 id="future-courses-header" class="font-size-18 mt-3 text-medium-emphasis w-100">
        Future courses
      </h3>
      <div class="mt-2 px-md-4 w-100">
        <v-radio-group
          v-model="pendingOptInNewCourses"
          aria-labelledby="future-courses-header"
          tabindex="-1"
          density="comfortable"
          hide-details
        >
          <v-radio
            id="all-future-courses-opt-in"
            :aria-label="null"
            color="primary"
            label="I want all my future courses to be opted into Course Capture by default"
            :value="true"
          />
          <v-radio
            id="choose-courses-opt-in"
            :aria-label="null"
            color="primary"
            label="I want to choose whether or not to opt in future courses to Course Capture"
            :value="false"
          />
        </v-radio-group>
      </div>
    </section>

    <section aria-labelledby="email-settings-header">
      <h3 id="email-settings-header" class="font-size-18 mt-6 text-medium-emphasis w-100">
        Email settings
      </h3>
      <div class="align-center d-flex px-md-4 w-100">
        <v-checkbox
          id="email-checkbox"
          v-model="emailReceive"
          :aria-label="null"
          color="primary"
          :disabled="isEmailDisabled"
          hide-details
        />
        <label class="font-size-16" for="email-checkbox">
          I want to receive emails from Course Capture (required if opted-in to current or future courses)
        </label>
      </div>
    </section>

    <div class="mt-4 px-md-4">
      <ProgressButton
        id="btn-course-capture-preferences-save"
        :action="save"
        aria-label="Save Course Capture preferences"
        density="comfortable"
        :disabled="isSaving || !isDirty"
        :in-progress="isSaving"
        :text="isSaving ? 'Saving' : 'Save'"
      />
      <v-btn
        id="btn-course-capture-preferences-cancel"
        aria-label="Cancel Course Capture preferences changes"
        class="ml-2"
        density="comfortable"
        :disabled="isSaving || !isDirty"
        text="Cancel"
        variant="outlined"
        @click="cancel"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref, watch} from 'vue'
import type {DiabloUser} from '@/lib/types'
import {alertScreenReader} from '@/lib/utils'
import {updateDoNotEmail, updateOptInNewCourses} from '@/api/user'
import ProgressButton from '@/components/util/ProgressButton.vue'

const user = defineModel<DiabloUser>({required: true})

const props = defineProps({
  /** If ANY course is opted-in or scheduled, parent passes true to enforce email on */
  disableEmailBecauseCourses: {
    required: true,
    type: Boolean
  },
  onUpdateUser: {
    required: true,
    type: Function
  }
})

const error = ref<string | undefined>()
const isSaving = ref(false)
const pendingDoNotEmail = ref<boolean>(false)
const pendingOptInNewCourses = ref<boolean>(false)

const emailReceive = computed<boolean>({
  get() {
    return !pendingDoNotEmail.value
  },
  set(value: boolean) {
    pendingDoNotEmail.value = !value
  }
})
const isEmailDisabled = computed(() =>
  pendingOptInNewCourses.value || props.disableEmailBecauseCourses
)
const isDirty = computed(() =>
  pendingOptInNewCourses.value !== user.value.optInNewCourses || pendingDoNotEmail.value !== user.value.doNotEmail
)

// Enforce “email must be on” when disabled
watch(isEmailDisabled, (mustEnable: boolean) => {
  if (mustEnable) {
    pendingDoNotEmail.value = false
  }
})

onMounted(() => resetPending())

function resetPending() {
  pendingOptInNewCourses.value = user.value.optInNewCourses
  pendingDoNotEmail.value = user.value.doNotEmail
}

function cancel() {
  error.value = undefined
  resetPending()
  alertScreenReader('Update canceled')
}

function save() {
  error.value = undefined
  isSaving.value = true
  const updates: Promise<unknown>[] = []
  if (pendingOptInNewCourses.value !== user.value.optInNewCourses) {
    updates.push(updateOptInNewCourses(user.value.uid, pendingOptInNewCourses.value))
  }
  if (pendingDoNotEmail.value !== user.value.doNotEmail) {
    updates.push(updateDoNotEmail(user.value.uid, pendingDoNotEmail.value))
  }
  return Promise.all(updates).then(() => {
    alertScreenReader('Course Capture preferences updated.')
  }).catch(() => {
    error.value = 'Failed to update Course Capture preferences.'
    alertScreenReader(error.value)
  }).finally(() => {
    isSaving.value = false
    return Promise.resolve(props.onUpdateUser()).then(resetPending)
  })
}
</script>
