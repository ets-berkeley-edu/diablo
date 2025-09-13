<template>
  <v-row
    align="center"
    aria-labelledby="recording-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12" class="pa-4 my-2" :class="{'bg-surface-light rounded': isEditing}">
      <h3 id="recording-type-header">
        <label v-if="isEditing && recordingTypeEditable" for="select-recording-type">Recording Type</label>
        <span v-if="!(isEditing && recordingTypeEditable)">Recording Type</span>
      </h3>
      <div v-if="!isEditing">
        <div id="recording-type-name" class="pl-4 pt-2">
          {{ labels[course.recordingType] }}
        </div>
        <v-btn
          v-if="!isEditing && recordingTypeEditable"
          id="btn-recording-type-edit"
          aria-label="Edit Recording Type"
          class="mt-3"
          @click="toggleIsEditing"
        >
          Edit
        </v-btn>
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
            {{ labels[recordingTypeOption] }}
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
import type {PropType} from 'vue'
import {computed, onMounted, ref} from 'vue'
import type {Course} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {updateRecordingType} from '@/api/course'
import {useContextStore} from '@/stores/context'
import ProgressButton from '@/components/util/ProgressButton.vue'

const props = defineProps({
  course: {
    required: true,
    type: Object as PropType<Course>
  },
  labels: {
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
const recordingType = ref(props.course.recordingType)
const recordingTypeOptions = ref<string[]>([])
const recordingTypeEditable = computed(() =>
  recordingTypeOptions.value.length > 1 &&
  (currentUser.isAdmin || props.course.recordingType !== 'presenter_presentation_audio_with_operator')
)

onMounted(() => {
  const meeting = props.course.meetings.eligible[0] || props.course.meetings.ineligible[0]
  recordingTypeOptions.value = meeting.room ? Object.keys(meeting.room.recordingTypeOptions || {}) : []
})

const cancel = () => {
  alertScreenReader('Recording type edit cancelled.')
  putFocusNextTick('btn-recording-type-edit')
  isEditing.value = false
  recordingType.value = props.course.recordingType
}

const onRecordingTypeChange = (option, idx) => {
  recordingType.value = recordingType.value === option ? recordingTypeOptions.value[idx - 1] : option
}

const save = () => {
  isSaving.value = true
  updateRecordingType(
    recordingType.value,
    props.course.sectionId,
    props.course.termId
  ).then(course => {
    const message = `Recording type updated to ${props.labels[recordingType.value]}.`
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
