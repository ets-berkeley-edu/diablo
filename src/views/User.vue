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
      <v-row v-if="user.uid" class="mx-4">
        <ToggleOptIn
          :term-id="config.currentTermId.toString()"
          section-id="all"
          :instructor-uids="[user.uid]"
          label="Opt in for current semester"
          :before-toggle="() => (isRefreshingCourses = true)"
          :on-toggle="refreshUser"
        />
      </v-row>
      <v-row v-if="user.uid" class="mx-4 mt-0 mb-2">
        <ToggleOptIn
          term-id="all"
          section-id="all"
          :instructor-uids="[user.uid]"
          label="Opt in for all semesters"
          :before-toggle="() => (isRefreshingCourses = true)"
          :on-toggle="refreshUser"
        />
      </v-row>
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
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {filter} from 'lodash'
import {mdiSchoolOutline} from '@mdi/js'
import {alertScreenReader, partitionCoursesByEligibility, putFocusNextTick} from '@/lib/utils'
import {getCourseCodes} from '@/lib/berkeley'
import {deleteUserNote, getUser, updateUserNote} from '@/api/user'
import {useContextStore} from '@/stores/context'
import CoursesDataTable from '@/components/course/CoursesDataTable.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import ProgressButton from '@/components/util/ProgressButton'
import ToggleOptIn from '@/components/course/ToggleOptIn.vue'

const contextStore = useContextStore()
const {config, currentUser, loading} = storeToRefs(contextStore)

const route = useRoute()
const uid = route.params.uid

const eligibleCourses = ref([])
const ineligibleCourses = ref([])
const isEditingNote = ref(false)
const isSavingNote = ref(false)
const isRefreshingCourses = ref(false)
const noteBody = ref('')
const user = ref({})

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
</script>
