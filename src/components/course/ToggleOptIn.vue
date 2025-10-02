<template>
  <v-switch
    v-model="hasOptedIn"
    class="toggle-opt-in"
    color="primary"
    density="compact"
    :disabled="courseStore.disableButtons"
    flat
    hide-details
    inset
    @update:model-value="toggleOptIn"
  >
    <template #label>
      <slot />
    </template>
  </v-switch>
</template>

<script lang="ts" setup>
import {storeToRefs} from 'pinia'
import type {Course} from '@/lib/types'
import {useCourseStore} from '@/stores/course'
import {toggleCourseOptIn, toggleInstructorOptIn} from '@/api/course'
import {useContextStore} from '@/stores/context'

const hasOptedIn = defineModel('hasOptedIn',{required: true, type: Boolean})
const instructorUID = defineModel('instructorUid',{required: false, type: String})

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const currentUser = useContextStore().currentUser

const toggleOptIn = (optIn: boolean | null) => {
  const afterToggle = (data: Course) => {
    courseStore.setCourse(data)
    courseStore.setDisableButtons(false)
  }
  if (instructorUID.value) {
    courseStore.setDisableButtons(true)
    toggleInstructorOptIn(
      instructorUID.value,
      !!optIn,
      course.value.sectionId,
      course.value.termId
    ).then(afterToggle)
  } else {
    if (currentUser.isAdmin) {
      courseStore.setDisableButtons(true)
      toggleCourseOptIn(
        !!optIn,
        course.value.sectionId,
        course.value.termId
      ).then(afterToggle)
    } else {
      throw Error('A non-admin user cannot opt-in a course with zero instructors')
    }
  }
}
</script>

<style>
.toggle-opt-in label {
  font-size: 1.2rem;
  font-weight: 500;
  padding-inline: 12px !important;
}
</style>
