<template>
  <div v-if="!loading">
    <v-card variant="outlined" class="elevation-1">
      <v-card-title>
        <PageTitle :icon="mdiSchoolOutline" :text="`${user.name} (${user.uid})`" />
      </v-card-title>

      <v-card-subtitle class="body-1 mb-4 ml-14 text-subtitle-1">
        <a :href="`mailto:${user.email}`" target="_blank">
          {{ user.email }}
          <span class="sr-only">(opens in new tab)</span>
        </a>
      </v-card-subtitle>

      <v-row class="mx-4">
        <ToggleOptOut
          :term-id="config.currentTermId.toString()"
          section-id="all"
          :instructor-uid="user.uid"
          :initial-value="!!user.hasOptedOutForTerm"
          :disabled="!!user.hasOptedOutForAllTerms"
          label="for current semester"
          :before-toggle="() => (refreshingCourses = true)"
          :on-toggle="refreshUser"
        />
      </v-row>

      <v-row class="mx-4 mt-0 mb-2">
        <ToggleOptOut
          term-id="all"
          section-id="all"
          :instructor-uid="user.uid"
          :initial-value="!!user.hasOptedOutForAllTerms"
          label="for all semesters"
          :before-toggle="() => (refreshingCourses = true)"
          :on-toggle="refreshUser"
        />
      </v-row>

      <Spinner v-if="refreshingCourses" />

      <div v-if="!refreshingCourses && eligibleCourses.length" id="user-courses-eligible">
        <CoursesDataTable
          class="pt-5"
          :courses="eligibleCourses"
          :include-room-column="true"
          :include-opt-out-column-for-uid="user.uid"
          :message-for-courses="summarize(eligibleCourses)"
          :refreshing="false"
        />
      </div>

      <div v-if="!refreshingCourses && ineligibleCourses.length" id="user-courses-ineligible">
        <h2 class="px-4">Courses not in a course capture classroom</h2>
        <CoursesDataTable
          class="pt-5"
          :courses="ineligibleCourses"
          :include-room-column="true"
          :message-for-courses="summarize(ineligibleCourses)"
          :refreshing="false"
        />
      </div>
    </v-card>

    <v-card v-if="currentUser.isAdmin" variant="outlined" class="elevation-1 mt-4">
      <v-card-title>Notes</v-card-title>

      <v-card-text v-if="!isEditingNote" id="note-body">
        {{ user.note || 'No notes.' }}
      </v-card-text>

      <v-card-actions v-if="!isEditingNote" class="px-4 pb-4">
        <v-btn
          id="btn-edit-note"
          variant="elevated"
          :disabled="isUpdatingNote"
          @click="editNote"
        >
          Edit
        </v-btn>
        <v-btn
          v-if="user.note"
          id="btn-delete-note"
          class="mx-3"
          variant="elevated"
          :disabled="isUpdatingNote"
          @click="deleteNote"
        >
          Delete
        </v-btn>
      </v-card-actions>

      <v-card-text v-if="isEditingNote">
        <v-textarea
          id="note-body-edit"
          v-model="noteBody"
          variant="outlined"
          hide-details="auto"
          density="compact"
          placeholder="Enter note text"
        />
      </v-card-text>

      <v-card-actions v-if="isEditingNote" class="px-4 pb-4">
        <v-btn
          id="btn-save-note"
          color="success"
          :disabled="!noteBody || isUpdatingNote"
          variant="elevated"
          @click="saveNote"
        >
          Save
        </v-btn>
        <v-btn
          id="btn-cancel-note"
          class="mx-3"
          variant="elevated"
          :disabled="isUpdatingNote"
          @click="cancelNote"
        >
          Cancel
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {alertScreenReader, getCourseCodes, partitionCoursesByEligibility} from '@/lib/utils'
import {getUser, deleteUserNote, updateUserNote} from '@/api/user'
import {useContextStore} from '@/stores/context'
import CoursesDataTable from '@/components/course/CoursesDataTable.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import Spinner from '@/components/util/Spinner.vue'
import ToggleOptOut from '@/components/course/ToggleOptOut.vue'
import {storeToRefs} from 'pinia'
import {filter} from 'lodash'
import {mdiSchoolOutline} from '@mdi/js'

const contextStore = useContextStore()
const {config, currentUser, loading} = storeToRefs(contextStore)

const route = useRoute()
const uid = route.params.uid

const user = ref({})
const eligibleCourses = ref([])
const ineligibleCourses = ref([])
const isEditingNote = ref(false)
const isUpdatingNote = ref(false)
const noteBody = ref('')
const refreshingCourses = ref(false)

function summarize(courses) {
  let message = `${courses.length} course${courses.length === 1 ? '' : 's'}.`
  const scheduled = filter(courses, 'scheduled')
  if (scheduled && scheduled.length) {
    return `${message} ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'} recordings scheduled.`
  } else {
    return message
  }
}

onMounted(() => {
  contextStore.loadingStart()
  refreshUser()
})

const cancelNote = () => {
  noteBody.value = user.value.note
  isEditingNote.value = false
  isUpdatingNote.value = false
  alertScreenReader('Note edit canceled.')
}

const deleteNote = () => {
  isUpdatingNote.value = true
  deleteUserNote(uid).then(() => {
    user.value.note = noteBody.value = null
    isEditingNote.value = false
    isUpdatingNote.value = false
    alertScreenReader('Note deleted.')
  })
}

const editNote = () => {
  isEditingNote.value = true
  alertScreenReader('Editing note.')
}

const refreshUser = () => {
  getUser(uid).then(data => {
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

    contextStore.loadingComplete()
    refreshingCourses.value = false
  })
}

const saveNote = () => {
  isUpdatingNote.value = true
  updateUserNote(uid, noteBody.value).then(data => {
    user.value.note = noteBody.value = data.note
    isEditingNote.value = false
    isUpdatingNote.value = false
    alertScreenReader('Note updated.')
  })
}
</script>