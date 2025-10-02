<template>
  <v-row
    align="center"
    aria-labelledby="recording-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12">
      <h3 id="recording-type-header">
        Recording Type
      </h3>
      <div v-if="isEditing" class="ml-2 mt-2">
        <div
          v-if="recordingTypeOptions.length > 1"
          id="select-recording-type"
          :aria-activedescendant="`radio-recording-type-${recordingType}`"
          role="radiogroup"
          tabindex="0"
        >
          <v-radio-group
            v-model="recordingType"
            aria-labelledby="recording-type-header"
            color="primary"
            density="compact"
            hide-details
          >
            <v-radio
              v-for="recordingTypeOption in recordingTypeOptions"
              :id="`radio-recording-type-${recordingTypeOption}`"
              :key="recordingTypeOption"
              :label="displayLabels[recordingTypeOption]"
              :value="recordingTypeOption"
            />
          </v-radio-group>
        </div>
      </div>
      <div v-if="!isEditing">
        <div class="ml-2 mt-2">
          <span id="recording-type-name" class="font-weight-medium">{{ displayLabels[course.recordingType] }}</span>
          <span v-if="recordingTypeOptions.length === 1" class="text-medium-emphasis">&nbsp;(the only recording type available)</span>
        </div>
      </div>
      <div v-if="recordingTypeOptions.length > 1" class="ml-2">
        <div v-if="isEditing" class="mt-3">
          <ProgressButton
            id="btn-recording-type-save"
            :action="update"
            aria-label="Save recording type"
            density="comfortable"
            :disabled="!recordingType || isSaving"
            :in-progress="isSaving"
            :text="isSaving ? 'Saving' : 'Save'"
          />
          <v-btn
            id="btn-recording-type-cancel"
            aria-label="Cancel edit"
            class="ml-2"
            density="comfortable"
            :disabled="isSaving"
            text="Cancel"
            variant="outlined"
            @click="cancel"
          />
        </div>
        <v-expand-transition v-if="recordingTypeOptions.length > 1 && !isEditing">
          <v-btn
            v-if="canUserEdit"
            id="btn-recording-type-edit"
            aria-label="Edit recording type"
            class="mt-3"
            color="primary"
            density="comfortable"
            :disabled="disableButtons"
            text="Edit"
            @click="edit"
          />
        </v-expand-transition>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {find, get} from 'lodash'
import {storeToRefs} from 'pinia'
import type {Course} from '@/lib/types'
import {alertScreenReader} from '@/lib/utils'
import {updateRecordingType} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import ProgressButton from '@/components/util/ProgressButton.vue'

const courseStore = useCourseStore()
const {course, disableButtons} = storeToRefs(courseStore)
const canUserEdit = computed(() => {
  if (currentUser.isAdmin) {
    return course.value.hasOptedIn || !!find(course.value.instructors, 'hasOptedIn')
  } else {
    const instructor = find(course.value.instructors, ['uid', currentUser.uid])
    return get(instructor, 'hasOptedIn', false)
  }
})
const currentUser = useContextStore().currentUser
const displayLabels = {
  presenter_presentation_audio: 'Camera Without Operator',
  presenter_presentation_audio_with_operator: `Camera With Operator ($${useContextStore().config.courseCapturePremiumCost} fee)`
}
const isEditing = ref(false)
const isSaving = ref(false)
const recordingType = ref<string>(course.value.recordingType)
const recordingTypeOptions = ref<string[]>([])

onMounted(() => {
  const meeting = course.value.meetings.eligible[0] || course.value.meetings.ineligible[0]
  recordingTypeOptions.value = meeting.room ? Object.keys(meeting.room.recordingTypeOptions || {}) : []
})

const cancel = () => {
  isEditing.value = false
  recordingType.value = course.value.recordingType
  courseStore.setDisableButtons(false)
  alertScreenReader('Update canceled')
}

const edit = () => {
  courseStore.setDisableButtons(true)
  isEditing.value = true
  alertScreenReader('Ready to edit recording type')
}

const update = () => {
  if (recordingType.value) {
    isSaving.value = true
    updateRecordingType(recordingType.value, course.value.sectionId, course.value.termId).then((data: Course) => {
      courseStore.setCourse(data)
      recordingType.value = course.value.recordingType
      isEditing.value = false
      isSaving.value = false
      courseStore.setDisableButtons(false)
      alertScreenReader('Recording type updated.')
    })
  }
}
</script>
