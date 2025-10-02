<template>
  <v-row
    align="center"
    aria-labelledby="recording-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12">
      <div v-if="recordingTypeOptions.length > 1">
        <h3 id="recording-type-header">
          <label v-if="recordingTypeOptions.length > 1" for="select-recording-type">Recording Type</label>
        </h3>
        <div
          v-if="recordingTypeOptions.length > 1"
          id="select-recording-type"
          :aria-activedescendant="`radio-recording-type-${recordingType}`"
          class="mt-2"
          role="radiogroup"
          tabindex="0"
        >
          <v-radio-group
            v-model="recordingType"
            color="primary"
            density="comfortable"
            :disabled="courseStore.disableButtons"
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
      <div v-if="recordingTypeOptions.length === 1">
        <h3 id="recording-type-header">Recording Type</h3>
        <div class="ml-2 mt-2">
          <span id="recording-type-name" class="font-weight-medium">{{ displayLabels[course.recordingType] }}</span>
          <span class="text-medium-emphasis">&nbsp;(the only recording type available)</span>
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'

const recordingType = defineModel({required: true, type: String})
const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const displayLabels = {
  presenter_presentation_audio: 'Camera Without Operator',
  presenter_presentation_audio_with_operator: `Camera With Operator ($${useContextStore().config.courseCapturePremiumCost} fee)`
}
const recordingTypeOptions = ref<string[]>([])

onMounted(() => {
  const meeting = course.value.meetings.eligible[0] || course.value.meetings.ineligible[0]
  recordingTypeOptions.value = meeting.room ? Object.keys(meeting.room.recordingTypeOptions || {}) : []
  if (recordingTypeOptions.value.length === 1) {
    recordingType.value = recordingTypeOptions.value[0]
    course.value.recordingType = recordingType.value
  }
})
</script>
