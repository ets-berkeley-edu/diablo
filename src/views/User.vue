<template>
  <div v-if="!loading">
    <v-card class="border-sm">
      <v-card-title>
        <PageTitle :icon="mdiSchoolOutline" :text="`${user.name} (${user.uid})`" />
      </v-card-title>
      <v-card-subtitle class="body-1 mb-4 ml-14 text-subtitle-1">
        <a :href="`mailto:${user.email}`" target="_blank">
          {{ user.email }}
        </a>
      </v-card-subtitle>
      <div v-if="eligibleCourses.length" id="user-courses-eligible">
        <CoursesDataTable
          class="pt-5"
          :courses="eligibleCourses"
          :include-opt-in-column-for-uid="[user.uid]"
          :include-room-column="true"
          :message-for-courses="summarize(eligibleCourses)"
          :refreshing="isRefreshingCourses"
          :show-opt-in="true"
        />
      </div>
      <div v-if="!isRefreshingCourses && ineligibleCourses.length" id="user-courses-ineligible">
        <h2 class="px-4">Courses not in a course capture classroom</h2>
        <CoursesDataTable
          class="pt-5"
          :courses="ineligibleCourses"
          :include-room-column="true"
          :message-for-courses="summarize(ineligibleCourses)"
          :refreshing="false"
          :show-opt-in="false"
        />
      </div>
    </v-card>
    <v-card v-if="currentUser.isAdmin" class="border-sm mt-4">
      <v-card-title>Preferences</v-card-title>
      <v-card-text>
        <section aria-labelledby="future-courses-header" class="py-5">
          <h2 id="future-courses-header" class="pa-4 text-medium-emphasis w-100">
            Future courses
          </h2>
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

        <v-divider class="my-2" />

        <section aria-labelledby="email-settings-header" class="py-5">
          <h2 id="email-settings-header" class="pa-4 text-medium-emphasis w-100">
            Email settings
          </h2>
          <div class="px-md-4 w-100">
            <v-checkbox
              id="email-checkbox"
              v-model="emailReceive"
              :disabled="isEmailDisabled"
              :aria-labelledby="'email-settings-header'"
              label="I want to receive emails from Course Capture (required if opted-in to current or future courses)"
              @update:model-value="onEmailReceiveChange"
            />
          </div>
        </section>
      </v-card-text>
    </v-card>
    <v-card v-if="currentUser.isAdmin" class="border-sm mt-4">
      <v-card-title>Notes</v-card-title>
      <v-card-text v-if="!isEditingNote" id="note-body">
        {{ user.note || 'No notes.' }}
      </v-card-text>
      <v-card-text v-if="isEditingNote">
        <v-textarea
          id="note-body-edit"
          v-model="noteBody"
          aria-describedby="undefined"
          density="compact"
          hide-details
          placeholder="Enter note text"
          variant="outlined"
        />
      </v-card-text>
      <v-card-actions v-if="!isEditingNote" class="px-4 pb-4">
        <v-btn
          id="btn-edit-note"
          :disabled="isSavingNote"
          @click="editNote"
        >
          Edit
        </v-btn>
        <v-btn
          v-if="user.note"
          id="btn-delete-note"
          class="mx-3"
          :disabled="isSavingNote"
          @click="deleteNote"
        >
          Delete
        </v-btn>
      </v-card-actions>
      <v-card-actions v-if="isEditingNote" class="px-4 pb-4">
        <ProgressButton
          id="btn-save-note"
          :action="saveNote"
          :disabled="!noteBody || isSavingNote"
          :in-progress="isSavingNote"
          :text="isSavingNote ? 'Saving' : 'Save'"
        />
        <v-btn
          id="btn-cancel-note"
          class="ml-2"
          :disabled="isSavingNote"
          variant="text"
          @click="cancelNote"
        >
          Cancel
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import {computed, onMounted, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {filter} from 'lodash'
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
  const message = `${courses.length} course${courses.length === 1 ? '' : 's'}.`
  const scheduled = filter(courses, 'scheduled')
  if (scheduled && scheduled.length) {
    return `${message} ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'} recordings scheduled.`
  } else {
    return message
  }
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
