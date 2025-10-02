<template>
  <div v-if="currentUser.isAdmin" class="mt-8 mx-1">
    <h3>Notes</h3>
    <div
      v-if="!isEditing"
      id="note-body"
      :class="isEmpty(course.note) ? 'my-2' : 'mb-4 mt-2'"
      class="font-size-16 my-2"
    >
      {{ course.note }}
    </div>
    <div v-if="!isEditing">
      <v-btn
        id="btn-edit-note"
        aria-label="Edit note"
        :disabled="isSaving"
        :text="isEmpty(course.note) ? 'Create' : 'Edit'"
        variant="outlined"
        @click="editNote"
      />
      <v-btn
        v-if="size(course.note)"
        id="btn-delete-note"
        aria-label="Delete Note"
        class="ml-1"
        color="red-lighten-2"
        :disabled="isSaving"
        text="Delete"
        variant="flat"
        @click="deleteNote"
      />
    </div>
    <div v-if="isEditing" class="mt-3">
      <v-textarea
        id="note-body-edit"
        v-model="noteBody"
        :aria-describedby="undefined"
        density="compact"
        hide-details
        placeholder="Enter note text"
        variant="outlined"
      />
    </div>
    <div v-if="isEditing" class="mt-3">
      <ProgressButton
        id="btn-save-note"
        :action="saveNote"
        aria-label="Save Note"
        :disabled="isSaving"
        :in-progress="isSaving"
        :text="isSaving ? 'Saving' : 'Save'"
      />
      <v-btn
        id="btn-cancel-note"
        aria-label="Cancel Note Edit"
        class="ml-2"
        :disabled="isSaving"
        text="Cancel"
        variant="text"
        @click="cancelNote"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import {isEmpty, size, trim} from 'lodash'
import {ref, watch} from 'vue'
import {storeToRefs} from 'pinia'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {deleteCourseNote, updateCourseNote} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import ProgressButton from '@/components/util/ProgressButton.vue'

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const {currentUser} = useContextStore()
const isEditing = ref(false)
const isSaving = ref(false)
const noteBody = ref<string | undefined>()

watch(isEditing, courseStore.setDisableButtons)
watch(isSaving, courseStore.setDisableButtons)

const cancelNote = () => {
  noteBody.value = course.value.note
  isEditing.value = false
  isSaving.value = false
  alertScreenReader('Canceled edit.')
  putFocusNextTick('btn-edit-note')
}

const deleteNote = () => {
  isSaving.value = true
  deleteCourseNote(course.value.termId, course.value.sectionId).then(() => {
    course.value.note = undefined
    noteBody.value = undefined
    isSaving.value = false
    alertScreenReader('Note deleted.')
    putFocusNextTick('btn-edit-note')
  })
}

const editNote = () => {
  noteBody.value = course.value.note
  isEditing.value = true
  putFocusNextTick('note-body-edit')
}

const saveNote = () => {
  const afterNoteUpdate = (note: string | undefined) => {
    course.value.note = note
    noteBody.value = note
    isEditing.value = false
    isSaving.value = false
    alertScreenReader('Note updated.')
    putFocusNextTick('btn-edit-note')
  }
  noteBody.value = trim(noteBody.value)
  if (noteBody.value) {
    isSaving.value = true
    updateCourseNote(course.value.termId, course.value.sectionId, noteBody.value).then(afterNoteUpdate)
  } else {
    deleteCourseNote(course.value.termId, course.value.sectionId).then(() => afterNoteUpdate(undefined))
  }
}
</script>
