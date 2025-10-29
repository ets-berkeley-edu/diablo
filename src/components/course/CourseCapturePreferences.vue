<template>
  <div>
    <section aria-labelledby="future-courses-header">
      <h2 id="future-courses-header" class="mt-3 text-medium-emphasis w-100">
        Future courses
      </h2>
      <div class="mt-2 px-md-4 w-100">
        <v-radio-group
          v-model="futureCoursesPref"
          aria-labelledby="future-courses-header"
          density="comfortable"
          hide-details
          @update:model-value="onFutureCoursesPreferenceChange"
        >
          <v-radio
            id="all-future-courses-opt-in"
            value="all"
            color="primary"
            label="I want all my future courses to be opted into Course Capture by default"
            :aria-label="null"
          />
          <v-radio
            id="choose-courses-opt-in"
            value="choose"
            color="primary"
            label="I want to choose whether or not to opt in future courses to Course Capture"
            :aria-label="null"
          />
        </v-radio-group>
      </div>
    </section>

    <v-divider class="mr-10 my-6" />

    <section aria-labelledby="email-settings-header">
      <h2 id="email-settings-header" class="mt-4 text-medium-emphasis w-100">
        Email settings
      </h2>
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
import {computed, ref, watch} from 'vue'
import {alertScreenReader} from '@/lib/utils'
import {updateDoNotEmail, updateOptInNewCourses} from '@/api/user'

const props = defineProps({
  /** If ANY course is opted-in or scheduled, parent passes true to enforce email on */
  disableEmailBecauseCourses: {
    required: true,
    type: Boolean
  },
  initialDoNotEmail: {
    required: true,
    type: Boolean
  },
  initialOptInNewCourses: {
    required: true,
    type: Boolean
  },
  uid: {
    required: true,
    type: String
  }
})

const futureCoursesPref = ref(props.initialOptInNewCourses ? 'all' : 'choose')
const emailReceive = ref(!props.initialDoNotEmail)

const isEmailDisabled = computed(() =>
  futureCoursesPref.value === 'all' || props.disableEmailBecauseCourses
)

// Enforce “email must be on” when disabled;
watch(isEmailDisabled, (mustEnable) => {
  if (mustEnable) {
    emailReceive.value = true
    if (props.initialDoNotEmail) {
      onEmailReceiveChange(true, {force: true})
    }
  }
})

function onFutureCoursesPreferenceChange(value: string) {
  const optInNewCourses = value === 'all'
  updateOptInNewCourses(String(props.uid), {optInNewCourses})
    .then((prefs) => {
      const {optInNewCourses: optAll, doNotEmail} = prefs || {}
      futureCoursesPref.value = optAll ? 'all' : 'choose'
      emailReceive.value = !(doNotEmail)
      alertScreenReader('Future courses preference updated.')
    })
    .catch(() => {
      futureCoursesPref.value = props.initialOptInNewCourses ? 'all' : 'choose'
      alertScreenReader('Failed to update future courses preference.')
    })
}

function onEmailReceiveChange(value: boolean, {force = false}: {force?: boolean} = {}) {
  if (isEmailDisabled.value && !force) {
    emailReceive.value = true
    return
  }
  updateDoNotEmail(String(props.uid), {doNotEmail: !value})
    .then((prefs) => {
      emailReceive.value = !prefs.doNotEmail
      futureCoursesPref.value = prefs.optInNewCourses ? 'all' : 'choose'

      alertScreenReader('Email preference updated.')
    })
    .catch(() => {
      // revert to local
      emailReceive.value = !props.initialDoNotEmail
      alertScreenReader('Failed to update email preference.')
    })
}
</script>
