<template>
  <div v-if="!loading" class="px-4 py-6">
    <v-card class="border-sm py-3 px-6 pr-12">
      <v-card-title class="pb-0">
        <PageTitle :icon="mdiSchoolOutline" :text="`${user.name} (${user.uid})`" />
      </v-card-title>
      <v-card-subtitle class="font-size-24 pl-16">
        <a :href="`mailto:${user.email}`" target="_blank">
          {{ user.email }}
        </a>
      </v-card-subtitle>
      <v-card-text>
        <div v-if="eligibleCourses.length" id="user-courses-eligible">
          <CoursesDataTable
            :courses="eligibleCourses"
            :include-opt-in-column-for-uid="[user.uid]"
            :include-room-column="true"
            :message-for-courses="summarize(eligibleCourses)"
            :refreshing="isRefreshingCourses"
            :show-opt-in="false"
          />
        </div>
        <div
          v-if="!isRefreshingCourses && ineligibleCourses.length"
          id="user-courses-ineligible"
          class="mb-2 mt-6"
        >
          <h2 class="font-size-24">Courses not in a course capture classroom</h2>
          <CoursesDataTable
            :courses="ineligibleCourses"
            :include-room-column="true"
            :message-for-courses="summarize(ineligibleCourses)"
            :refreshing="false"
            :show-opt-in="false"
          />
        </div>
      </v-card-text>
    </v-card>
    <v-card v-if="currentUser.isAdmin" class="border-sm mt-8 pt-6 px-6">
      <v-card-title>
        <h2 class="font-size-24">Preferences</h2>
      </v-card-title>
      <v-card-text>
        <section aria-labelledby="future-courses-header" class="mt-3">
          <h3 id="future-courses-header" class="font-size-18 text-medium-emphasis">
            Future courses
          </h3>
          <div class="px-md-4 w-100">
            <v-radio-group
              v-model="futureCoursesPref"
              :aria-labelledby="'future-courses-header'"
              @update:model-value="onFutureCoursesPreferenceChange"
            >
              <v-radio
                id="all-future-courses-opt-in"
                value="all"
                color="primary"
                label="I want all my future courses to be opted into Course Capture by default"
              />
              <v-radio
                id="choose-courses-opt-in"
                value="choose"
                color="primary"
                label="I want to choose whether or not to opt in future courses to Course Capture"
              />
            </v-radio-group>
          </div>
        </section>
        <section aria-labelledby="email-settings-header">
          <h3 id="email-settings-header" class="font-size-18 text-medium-emphasis">
            Email settings
          </h3>
          <div class="px-md-4 w-100">
            <v-checkbox
              id="email-checkbox"
              v-model="emailReceive"
              color="primary"
              :disabled="isEmailDisabled"
              :aria-labelledby="'email-settings-header'"
              label="I want to receive emails from Course Capture (required if opted-in to current or future courses)"
              @update:model-value="onEmailReceiveChange"
            />
          </div>
        </section>
      </v-card-text>
    </v-card>
    <v-card v-if="currentUser.isAdmin" class="border-sm mt-8 pa-6">
      <v-card-title>
        <h2 class="font-size-24">Notes</h2>
      </v-card-title>
      <v-card-text v-if="!isEditingNote && user.note" id="note-body">
        {{ user.note }}
      </v-card-text>
      <v-card-text v-if="isEditingNote" class="pr-16">
        <v-textarea
          id="note-body-edit"
          v-model="noteBody"
          aria-describedby="undefined"
          color="primary"
          density="compact"
          hide-details
          placeholder="Enter note text"
          variant="outlined"
        />
      </v-card-text>
      <v-card-actions v-if="!isEditingNote" class="px-4 pb-4">
        <v-btn
          id="btn-edit-note"
          color="primary"
          :disabled="isSavingNote"
          :text="isEmpty(trim(user.note)) ? 'Create' : 'Edit'"
          variant="flat"
          @click="editNote"
        />
        <v-btn
          v-if="user.note"
          id="btn-delete-note"
          color="red"
          :disabled="isSavingNote"
          text="Delete"
          variant="outlined"
          @click="deleteNote"
        />
      </v-card-actions>
      <v-card-actions v-if="isEditingNote" class="pb-4 pt-0 px-4">
        <ProgressButton
          id="btn-save-note"
          :action="saveNote"
          :disabled="!noteBody || isSavingNote"
          :in-progress="isSavingNote"
          :text="isSavingNote ? 'Saving' : 'Save'"
        />
        <v-btn
          id="btn-cancel-note"
          class="ml-1"
          :disabled="isSavingNote"
          text="Cancel"
          variant="text"
          @click="cancelNote"
        />
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import {computed, onMounted, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {filter, isEmpty, trim} from 'lodash'
import {mdiSchoolOutline} from '@mdi/js'
import {alertScreenReader, partitionCoursesByEligibility, putFocusNextTick} from '@/lib/utils'
import {getCourseCodes} from '@/lib/berkeley'
import {deleteUserNote, getUser, updateDoNotEmail, updateOptInNewCourses, updateUserNote} from '@/api/user'
import {useContextStore} from '@/stores/context'
import CoursesDataTable from '@/components/course/CoursesDataTable.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import ProgressButton from '@/components/util/ProgressButton'

const contextStore = useContextStore()
const {currentUser, loading} = storeToRefs(contextStore)

const route = useRoute()
const uid = route.params.uid

const eligibleCourses = ref([])
const ineligibleCourses = ref([])
const isEditingNote = ref(false)
const isSavingNote = ref(false)
const isRefreshingCourses = ref(false)
const noteBody = ref('')
const user = ref({})

const futureCoursesPref = ref(null)
const emailReceive = ref(true)

const isEmailDisabled = computed(() => {
  return futureCoursesPref.value === 'all'
})

// If email must be disabled, auto-uncheck and sync server if needed
watch(isEmailDisabled, (disabled) => {
  if (disabled) {
    emailReceive.value = false
    if (user.value?.doNotEmail) {
      onEmailReceiveChange(false, {force: true})
    }
  }
})

contextStore.loadingStart()

onMounted(() => {
  refreshUser().then(() => {
    contextStore.loadingComplete(`${user.value.name} Profile`)
  })
})

const cancelNote = () => {
  noteBody.value = user.value.note
  isEditingNote.value = false
  isSavingNote.value = false
  alertScreenReader('Note edit canceled.')
}

const deleteNote = () => {
  isSavingNote.value = true
  deleteUserNote(uid).then(() => {
    user.value.note = noteBody.value = null
    isEditingNote.value = false
    isSavingNote.value = false
    alertScreenReader('Note deleted.')
  })
}

const editNote = () => {
  isEditingNote.value = true
  putFocusNextTick('note-body-edit')
}

const refreshUser = () => {
  return getUser(uid).then(data => {
    user.value = data
    data.courses.forEach(course => {
      course.courseCodes = getCourseCodes(course)
    })
    noteBody.value = data.note
    eligibleCourses.value = []
    ineligibleCourses.value = []
    partitionCoursesByEligibility(
      data.courses,
      eligibleCourses.value,
      ineligibleCourses.value
    )
    const allCourses = [...eligibleCourses.value, ...ineligibleCourses.value]

    allCourses.forEach(course => {
      const eligibleLen = course.meetings?.eligible?.length || 0
      course.statusLabel = course.deletedAt
        ? 'Canceled'
        : (course.scheduled
          ? 'Scheduled'
          : (eligibleLen > 0
            ? (course.hasOptedIn ? 'Pending' : 'Not Opted In')
            : 'Not Eligible'))
    })
    futureCoursesPref.value = user.value.optInNewCourses ? 'all' : 'choose'
    emailReceive.value = !user.value.doNotEmail
    isRefreshingCourses.value = false
  })
}

const saveNote = () => {
  isSavingNote.value = true
  updateUserNote(uid, noteBody.value).then(data => {
    user.value.note = noteBody.value = data.note
    isEditingNote.value = false
    isSavingNote.value = false
    alertScreenReader('Note updated.')
  })
}

const summarize = courses => {
  let message
  const scheduled = filter(courses, 'scheduled')
  if (scheduled && scheduled.length) {
    message = `${courses.length} course${courses.length === 1 ? '' : 's'}.`
    message = `${message} ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'} recordings scheduled.`
  }
  return message
}

const onFutureCoursesPreferenceChange = (value) => {
  const optInNewCourses = value === 'all'
  updateOptInNewCourses(uid, {optInNewCourses})
    .then((prefs) => {
      const {optInNewCourses: optAll, doNotEmail} = prefs || {}
      futureCoursesPref.value = optAll ? 'all' : 'choose'
      user.value.optInNewCourses = !!optAll

      user.value.doNotEmail = doNotEmail
      emailReceive.value = doNotEmail

      alertScreenReader('Future courses preference updated.')
    })
    .catch(() => {
      // revert to server-known state
      futureCoursesPref.value = user.value.optInNewCourses ? 'all' : 'choose'
      alertScreenReader('Failed to update future courses preference.')
    })
}

const onEmailReceiveChange = (value, {force = false} = {}) => {
  if (isEmailDisabled.value && !force) {
    emailReceive.value = false
    return
  }
  updateDoNotEmail(uid, {doNotEmail: !value})
    .then((prefs) => {
      user.value.doNotEmail = !prefs.doNotEmail
      emailReceive.value = !prefs.doNotEmail

      user.value.optInNewCourses = prefs.optInNewCourses
      futureCoursesPref.value = prefs.optInNewCourses ? 'all' : 'choose'

      alertScreenReader('Email preference updated.')
    })
    .catch(() => {
      emailReceive.value = !user.value.doNotEmail
      alertScreenReader('Failed to update email preference.')
    })
}

</script>
