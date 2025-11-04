<template>
  <v-switch
    :id="id"
    v-model="hasOptedIn"
    :base-color="isToggling && hasOptedIn ? 'primary' : undefined"
    :class="{'toggle-focused': isFocused || isToggling, 'toggle-not-focused': !isFocused && !isToggling}"
    class="toggle-opt-in"
    color="primary"
    density="compact"
    :disabled="courseStore.disableButtons"
    flat
    hide-details
    inset
    :label="label"
    @update:focused="(focused: boolean) => isFocused = focused"
    @update:model-value="toggleOptIn"
  />
</template>

<script lang="ts" setup>
import {storeToRefs} from 'pinia'
import {ref} from 'vue'
import type {Course} from '@/lib/types'
import {putFocusNextTick} from '@/lib/utils'
import {toggleCourseOptIn, toggleInstructorOptIn} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'

const props = defineProps({
  id: {
    required: true,
    type: String
  },
  label: {
    default: undefined,
    required: false,
    type: String
  }
})

const hasOptedIn = defineModel('hasOptedIn',{required: true, type: Boolean})
const instructorUID = defineModel('instructorUid',{required: false, type: String})

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const currentUser = useContextStore().currentUser
const isFocused = ref(false)
const isToggling = ref(false)

const toggleOptIn = (optIn: boolean | null) => {
  const afterToggle = (data: Course) => {
    courseStore.setCourse(data)
    courseStore.setDisableButtons(false)
    putFocusNextTick(props.id)
    setTimeout(() => {
      isToggling.value = false
    }, 800)
  }
  isToggling.value = true
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
.toggle-focused {
  border: 2px solid #424689;
  border-radius: 50px;
  margin-right: 2px;
}
.toggle-not-focused {
  border: 2px solid transparent;
  margin-right: 2px;
}
.toggle-opt-in {
  padding: 0 3px;
}
.toggle-opt-in label {
  font-size: 1.2rem;
  font-weight: 500;
}
</style>
