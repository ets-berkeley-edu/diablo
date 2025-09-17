<template>
  <v-row
    align="center"
    aria-labelledby="recording-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12" :class="{'bg-surface-light rounded': isEditing}">
      <h3 id="recording-type-header">
        <label v-if="isEditing && recordingTypeEditable" for="select-recording-type">Recording Type</label>
        <span v-if="!(isEditing && recordingTypeEditable)">Recording Type</span>
      </h3>
      <div v-if="!isEditing" class="mt-2 pl-4">
        <div id="recording-type-name">
          {{ courseStore.displayLabels[course.recordingType] }}
        </div>
        <v-btn
          v-if="!isEditing && recordingTypeEditable"
          id="btn-recording-type-edit"
          aria-label="Edit Recording Type"
          class="elevation-1 mt-2"
          :disabled="courseStore.disableButtons"
          text="Edit"
          variant="outlined"
          @click="toggleIsEditing"
        />
      </div>
      <div
        v-if="isEditing && recordingTypeEditable"
        id="select-recording-type"
        :aria-activedescendant="`radio-recording-type-${recordingType}`"
        class="py-4"
        role="radiogroup"
        tabindex="0"
      >
        <div
          v-for="(recordingTypeOption, index) in recordingTypeOptions"
          :key="recordingTypeOption"
          class="d-flex flex-nowrap py-1"
        >
          <input
            :id="`radio-recording-type-${recordingTypeOption}`"
            :checked="recordingTypeOption === recordingType ? 'checked' : false"
            class="ml-1 mr-3"
            :disabled="isSaving"
            type="radio"
            :value="recordingTypeOption"
            @change="() => onRecordingTypeChange(recordingTypeOption, index)"
          >
          <label class="font-size-16 text-medium-emphasis" :for="`radio-recording-type-${recordingTypeOption}`">
            {{ courseStore.displayLabels[recordingTypeOption] }}
          </label>
        </div>
      </div>
      <div v-if="isEditing && recordingTypeEditable">
        <ProgressButton
          id="btn-recording-type-save"
          :action="save"
          aria-label="Save Recording Type"
          :disabled="isSaving"
          :in-progress="isSaving"
          :text="isSaving ? 'Saving' : 'Save'"
        />
        <v-btn
          id="btn-recording-type-cancel"
          aria-label="Cancel Recording Type Edit"
          class="ml-2"
          :disabled="isSaving"
          variant="text"
          @click="cancel"
        >
          Cancel
        </v-btn>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref, watch} from 'vue'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {updateRecordingType} from '@/api/course'
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
const recordingType = ref(course.recordingType)
const recordingTypeOptions = ref<string[]>([])
const recordingTypeEditable = computed(() =>
  recordingTypeOptions.value.length > 1 &&
  (currentUser.isAdmin || course.recordingType !== 'presenter_presentation_audio_with_operator')
)

watch(isEditing, courseStore.setDisableButtons)
watch(isSaving, courseStore.setDisableButtons)

onMounted(() => {
  const meeting = course.meetings.eligible[0] || course.meetings.ineligible[0]
  recordingTypeOptions.value = meeting.room ? Object.keys(meeting.room.recordingTypeOptions || {}) : []
})

const cancel = () => {
  alertScreenReader('Recording type edit cancelled.')
  putFocusNextTick('btn-recording-type-edit')
  isEditing.value = false
  recordingType.value = course.recordingType
}

const onRecordingTypeChange = (option, idx) => {
  recordingType.value = recordingType.value === option ? recordingTypeOptions.value[idx - 1] : option
}

const save = () => {
  isSaving.value = true
  updateRecordingType(
    recordingType.value,
    course.sectionId,
    course.termId
  ).then(course => {
    const message = `Recording type updated to ${courseStore.displayLabels[recordingType.value]}.`
    alertScreenReader(message)
    putFocusNextTick('btn-recording-type-edit')
    props.setModel(course)
    isEditing.value = false
    isSaving.value = false
  })
}

const toggleIsEditing = () => {
  isEditing.value = true
  putFocusNextTick('select-recording-type')
}
</script>
