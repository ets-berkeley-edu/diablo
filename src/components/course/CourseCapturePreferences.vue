<template>
  <div>
    <section aria-labelledby="future-courses-header">
      <h3 id="future-courses-header" class="font-size-18 mt-3 text-medium-emphasis w-100">
        Future courses
      </h3>
      <div class="mt-2 px-md-4 w-100">
        <v-radio-group
          v-model="user.optInNewCourses"
          aria-labelledby="future-courses-header"
          density="comfortable"
          hide-details
          @update:model-value="onUpdateOptInNewCourses"
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
      <div class="px-md-4 w-100">
        <v-checkbox
          id="email-checkbox"
          v-model="emailReceive"
          aria-labelledby="email-settings-header"
          color="primary"
          :disabled="isEmailDisabled"
          label="I want to receive emails from Course Capture (required if opted-in to current or future courses)"
          @update:model-value="onEmailReceiveChange"
        />
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import {computed, watch} from 'vue'
import type {DiabloUser} from '@/lib/types'
import {alertScreenReader} from '@/lib/utils'
import {updateDoNotEmail, updateOptInNewCourses} from '@/api/user'

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

const emailReceive = computed<boolean>({
  get() {
    return !user.value.doNotEmail
  },
  set(value: boolean) {
    user.value.doNotEmail = !value
  }
})
const isEmailDisabled = computed(() =>
  user.value.optInNewCourses || props.disableEmailBecauseCourses
)

// Enforce “email must be on” when disabled;
watch(isEmailDisabled, (mustEnable: boolean) => {
  if (mustEnable) {
    const initialDoNotEmail = user.value.doNotEmail
    emailReceive.value = true
    if (initialDoNotEmail) {
      onEmailReceiveChange(true, true)
    }
  }
})

const onUpdateOptInNewCourses = () => {
  updateOptInNewCourses(user.value.uid, user.value.optInNewCourses).then(() => {
    alertScreenReader('Future courses preference updated.')
  }).catch(() => {
    alertScreenReader('Failed to update future courses preference.')
  }).finally(() => {
    props.onUpdateUser()
  })
}

function onEmailReceiveChange(value: boolean | null, force?: boolean) {
  if (isEmailDisabled.value && !force) {
    emailReceive.value = true
    return
  }
  updateDoNotEmail(user.value.uid, !value).then(() => {
    alertScreenReader('Email preference updated.')
  }).catch(() => {
    alertScreenReader('Failed to update email preference.')
  }).finally(() => {
    props.onUpdateUser()
  })
}
</script>
