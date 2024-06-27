<template>
  <div v-if="!loading">
    <v-card outlined class="elevation-1">
      <v-card-title>
        <PageTitle icon="mdi-school-outline" :text="`${user.name} (${user.uid})`" />
      </v-card-title>
      <v-card-subtitle class="body-1 ml-8 pl-12">
        <a :href="`mailto:${user.email}`" target="_blank">{{ user.email }}<span class="sr-only"> (new browser tab will open)</span></a>
      </v-card-subtitle>
      <v-row class="mx-4">
        <ToggleOptOut
          :term-id="`${$config.currentTermId}`"
          section-id="all"
          :instructor-uid="user.uid"
          :initial-value="!!user.hasOptedOutForTerm"
          :disabled="!!user.hasOptedOutForAllTerms"
          label="Opt out for current semester"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="refreshUser"
        />
      </v-row>
      <v-row class="mx-4 mt-0 mb-2">
        <ToggleOptOut
          term-id="all"
          section-id="all"
          :instructor-uid="user.uid"
          :initial-value="!!user.hasOptedOutForAllTerms"
          label="Opt out for all semesters"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="refreshUser"
        />
      </v-row>
      <Spinner v-if="refreshingCourses" />
      <CoursesDataTable
        v-if="!refreshingCourses"
        class="pt-5"
        :courses="user.courses"
        :include-room-column="true"
        :include-opt-out-column-for-uid="user.uid"
        :message-for-courses="summarize(user.courses)"
        :refreshing="false"
      />
    </v-card>
    <v-card v-if="$currentUser.isAdmin" outlined class="elevation-1 mt-4">
      <v-card-title>
        Notes
      </v-card-title>
      <v-card-text v-if="!isEditingNote" id="note-body">
        {{ user.note || 'No notes.' }}
      </v-card-text>
      <v-card-actions v-if="!isEditingNote" class="px-4 pb-4">
        <v-btn
          id="btn-edit-note"
          :disabled="isUpdatingNote"
          @click="editNote"
        >
          Edit
        </v-btn>
        <v-btn
          v-if="user.note"
          id="btn-delete-note"
          class="mx-3"
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
          outlined
          hide-details="auto"
          density="compact"
          placeholder="Enter note text"
        >
        </v-textarea>
      </v-card-text>
      <v-card-actions v-if="isEditingNote" class="px-4 pb-4">
        <v-btn
          id="btn-save-note"
          color="success"
          :disabled="isUpdatingNote"
          @click="saveNote"
        >
          Save
        </v-btn>
        <v-btn
          id="btn-cancel-note"
          class="mx-3"
          :disabled="isUpdatingNote"
          @click="cancelNote"
        >
          Cancel
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import PageTitle from '@/components/util/PageTitle'
import Spinner from '@/components/util/Spinner'
import ToggleOptOut from '@/components/course/ToggleOptOut'
import Utils from '@/mixins/Utils'
import {deleteUserNote, getUser, updateUserNote} from '@/api/user'

export default {
  name: 'Room',
  mixins: [Context, Utils],
  components: {CoursesDataTable, PageTitle, Spinner, ToggleOptOut},
  data: () => ({
    isEditingNote: false,
    isUpdatingNote: false,
    noteBody: undefined,
    refreshingCourses: false,
    uid: undefined,
    user: undefined
  }),
  created() {
    this.$loading()
    this.uid = this.$_.get(this.$route, 'params.uid')
    this.refreshUser()
  },
  methods: {
    cancelNote() {
      this.noteBody = this.user.note
      this.isEditingNote = false
      this.isUpdatingNote = false
      this.alertScreenReader('Note edit canceled.')
    },
    deleteNote() {
      this.isUpdatingNote = true
      deleteUserNote(this.uid).then(() => {
        this.user.note = this.noteBody = null
        this.isEditingNote = false
        this.isUpdatingNote = false
        this.alertScreenReader('Note deleted.')
      })
    },
    editNote() {
      this.isEditingNote = true
      this.alertScreenReader('Editing note.')
    },
    refreshUser() {
      getUser(this.uid).then(user => {
        this.user = user
        this.$_.each(this.user.courses, course => {
          course.courseCodes = this.getCourseCodes(course)
        })
        this.noteBody = user.note
        this.$ready(this.user.name)
        this.refreshingCourses = false
      })
    },
    saveNote() {
      this.isUpdatingNote = true
      updateUserNote(this.uid, this.noteBody).then(data => {
        this.user.note = this.noteBody = data.note
        this.isEditingNote = false
        this.isUpdatingNote = false
        this.alertScreenReader('Note updated.')
      })
    },
  }
}
</script>
