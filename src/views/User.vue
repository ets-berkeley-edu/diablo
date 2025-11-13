<template>
  <div v-if="!loading">
    <v-card class="border-sm pr-md-12 pl-md-6 py-2">
      <v-card-title class="py-0">
        <PageTitle
          :icon="mdiSchoolOutline"
          :text="user.name ? `${user.name} (${user.uid})` : `UID: ${user.uid}`"
        />
      </v-card-title>
      <v-card-subtitle v-if="user.email" class="font-size-24 pt-0">
        <a class="ms-lg-13" :href="`mailto:${user.email}`" target="_blank">{{ user.email }}</a>
      </v-card-subtitle>
      <v-card-text>
        <div v-if="eligibleCourses.length" id="user-courses-eligible" class="border-sm pt-6 px-6 rounded">
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
          role="region"
          aria-labelledby="user-ineligible-header"
        >
          <v-expansion-panels class="border-sm rounded" flat rounded>
            <v-expansion-panel>
              <v-expansion-panel-title
                id="ineligible-courses-show-hide-btn"
                class="bg-primary"
                focusable
                hide-actions
              >
                <template #default="{expanded}">
                  <div class="align-center d-flex">
                    <div class="mr-2">
                      <v-icon
                        color="white"
                        :icon="expanded ? mdiMenuDown : mdiMenuRight"
                        size="x-large"
                      />
                    </div>
                    <div class="font-size-18">Courses not in a course capture classroom</div>
                  </div>
                </template>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <template #default>
                  <CoursesDataTable
                    id="user-ineligible-table"
                    :courses="ineligibleCourses"
                    :include-room-column="true"
                    :message-for-courses="summarize(ineligibleCourses)"
                    :refreshing="false"
                    :show-opt-in="false"
                  />
                </template>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </div>
      </v-card-text>
    </v-card>
    <v-card v-if="currentUser.isAdmin" class="border-sm mt-8 pt-6 px-6">
      <v-card-title>
        <h2 class="font-size-24">Preferences</h2>
      </v-card-title>
      <v-card-text>
        <CourseCapturePreferences
          v-model="user"
          :disable-email-because-courses="anyCourseOptedInOrScheduled"
          :on-update-user="refreshUser"
        />
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
          :disabled="isSavingNote || (!user.note && !trim(noteBody))"
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
import {computed, onMounted, ref} from 'vue'
import {filter, isEmpty, toString, trim} from 'lodash'
import {mdiMenuDown, mdiMenuRight, mdiSchoolOutline} from '@mdi/js'
import {storeToRefs} from 'pinia'
import {useRoute} from 'vue-router'
import {alertScreenReader, partitionCoursesByEligibility, putFocusNextTick} from '@/lib/utils'
import {deleteUserNote, getUser, updateUserNote} from '@/api/user'
import {getCourseCodes} from '@/lib/berkeley'
import {useContextStore} from '@/stores/context'
import CourseCapturePreferences from '@/components/course/CourseCapturePreferences.vue'
import CoursesDataTable from '@/components/course/CoursesDataTable.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import ProgressButton from '@/components/util/ProgressButton'

const contextStore = useContextStore()
const {currentUser, loading} = storeToRefs(contextStore)

const route = useRoute()
const eligibleCourses = ref([])
const ineligibleCourses = ref([])
const isEditingNote = ref(false)
const isRefreshingCourses = ref(false)
const isSavingNote = ref(false)
const noteBody = ref('')
const uid = toString(route.params.uid)
const user = ref({})

contextStore.loadingStart()

const isScheduled = (c) => Array.isArray(c.scheduled) ? c.scheduled.length > 0 : !!c.scheduled

const anyCourseOptedInOrScheduled = computed(() => {
  return [...eligibleCourses.value] .some(c => c.hasOptedIn || isScheduled(c))
})

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
    isRefreshingCourses.value = false
  })
}

const saveNote = () => {
  isSavingNote.value = true
  noteBody.value = trim(noteBody.value)
  if (noteBody.value) {
    updateUserNote(uid, noteBody.value).then(data => {
      user.value.note = noteBody.value = data.note
      isEditingNote.value = false
      isSavingNote.value = false
      alertScreenReader('Note updated.')
    })
  } else {
    deleteNote()
  }
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
</script>
