<template>
  <v-card v-if="currentUser.isAdmin" class="border-sm mt-4 mx-1">
    <v-card-title>
      <h3>Notes</h3>
    </v-card-title>
    <v-card-text v-if="!isEditing" id="note-body" class="font-size-16">
      <span v-if="course.notes">{{ course.note }}</span>
      <span v-if="!course.notes" class="text-medium-emphasis">No notes</span>
    </v-card-text>
    <v-card-actions v-if="!isEditing" class="px-4 pb-4">
      <v-btn
        id="btn-edit-note"
        aria-label="Edit note"
        :disabled="isSaving"
        variant="elevated"
        @click="editNote"
      >
        Edit
      </v-btn>
      <v-btn
        v-if="course.note"
        id="btn-delete-note"
        aria-label="Delete Note"
        class="ml-2"
        :disabled="isSaving"
        variant="elevated"
        @click="deleteNote"
      >
        Delete
      </v-btn>
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
      >
      </v-textarea>
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
        class="ml-2"
        :disabled="isSaving"
        variant="text"
        @click="cancelNote"
      >
        Cancel
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import {ref} from 'vue'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {deleteCourseNote, updateCourseNote} from '@/api/course'
import ProgressButton from '@/components/util/ProgressButton'
import {useContextStore} from '@/stores/context'

const props = defineProps({
  course: {
    required: true,
    type: Object
  },
  setModel: {
    required: true,
    type: Function
  }
})

const {currentUser} = useContextStore()
const isEditing = ref(false)
const isSaving = ref(false)
const noteBody = ref('')


const cancelNote = () => {
  noteBody.value = props.course.note
  isEditing.value = false
  isSaving.value = false
  alertScreenReader('Canceled edit.')
  putFocusNextTick('btn-edit-note')
}

const deleteNote = () => {
  isSaving.value = true
  deleteCourseNote(props.course.termId, props.course.sectionId)
    .then(() => {
      props.setModel(null)
      noteBody.value = null
      isSaving.value = false
      alertScreenReader('Note deleted.')
      putFocusNextTick('btn-edit-note')
    })
}

const editNote = () => {
  noteBody.value = props.course.note
  isEditing.value = true
  putFocusNextTick('note-body-edit')
}

const saveNote = () => {
  isSaving.value = true
  updateCourseNote(props.course.termId, props.course.sectionId, noteBody.value)
    .then(data => {
      noteBody.value = data.note
      props.setModel(data.note)
      isEditing.value = false
      isSaving.value = false
      alertScreenReader('Note updated.')
      putFocusNextTick('btn-edit-note')
    })
}
</script>
