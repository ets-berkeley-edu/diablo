<template>
  <v-card v-if="currentUser.isAdmin" class="border-sm mt-4 mx-1">
    <v-card-title>
      <h3>Notes</h3>
    </v-card-title>
    <v-card-text v-if="!isEditing" id="note-body" class="font-size-16">
      <span v-if="course.note">{{ course.note }}</span>
      <span v-if="!course.note" class="text-medium-emphasis">No notes.</span>
    </v-card-text>
    <v-card-actions v-if="!isEditing" class="px-4 pb-4">
      <v-btn
        id="btn-edit-note"
        aria-label="Edit note"
        :disabled="isSaving"
        text="Edit"
        variant="outlined"
        @click="editNote"
      />
      <v-btn
        v-if="course.note"
        id="btn-delete-note"
        aria-label="Delete Note"
        class="ml-1"
        color="red-lighten-2"
        :disabled="isSaving"
        text="Delete"
        variant="flat"
        @click="deleteNote"
      />
    </v-card-actions>
    <v-card-text v-if="isEditing">
      <v-textarea
        id="note-body-edit"
        v-model="noteBody"
        :aria-describedby="undefined"
        density="compact"
        hide-details
        placeholder="Enter note text"
        variant="outlined"
      />
    </v-card-text>
    <v-card-actions v-if="isEditing" class="px-4 pb-4">
      <ProgressButton
        id="btn-save-note"
        :action="saveNote"
        aria-label="Save Note"
        :disabled="!noteBody || isSaving"
        :in-progress="isSaving"
        :text="isSaving ? 'Saving' : 'Save'"
      />
      <v-btn
        id="btn-cancel-note"
        aria-label="Cancel Note Edit"
        class="ml-1"
        :disabled="isSaving"
        text="Cancel"
        variant="text"
        @click="cancelNote"
      />
    </v-card-actions>
  </v-card>
</template>

<script lang="ts" setup>
import {ref, watch} from 'vue'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {deleteCourseNote, updateCourseNote} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import ProgressButton from '@/components/util/ProgressButton.vue'

const props = defineProps({
  setModel: {
    required: true,
    type: Function
  }
})

const {currentUser} = useContextStore()
const courseStore = useCourseStore()
const course = courseStore.course
const isEditing = ref(false)
const isSaving = ref(false)
const noteBody = ref<string | undefined>()

watch(isEditing, courseStore.setDisableButtons)
watch(isSaving, courseStore.setDisableButtons)

const cancelNote = () => {
  noteBody.value = course.note
  isEditing.value = false
  isSaving.value = false
  alertScreenReader('Canceled edit.')
  putFocusNextTick('btn-edit-note')
}

const deleteNote = () => {
  isSaving.value = true
  deleteCourseNote(course.termId, course.sectionId)
    .then(() => {
      props.setModel(null)
      noteBody.value = undefined
      isSaving.value = false
      alertScreenReader('Note deleted.')
      putFocusNextTick('btn-edit-note')
    })
}

const editNote = () => {
  noteBody.value = course.note
  isEditing.value = true
  putFocusNextTick('note-body-edit')
}

const saveNote = () => {
  if (noteBody.value) {
    isSaving.value = true
    updateCourseNote(course.termId, course.sectionId, noteBody.value).then(data => {
      noteBody.value = data.note
      props.setModel(data.note)
      isEditing.value = false
      isSaving.value = false
      alertScreenReader('Note updated.')
      putFocusNextTick('btn-edit-note')
    })
  }
}
</script>
