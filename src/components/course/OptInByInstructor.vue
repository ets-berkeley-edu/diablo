<template>
  <div class="align-center d-flex">
    <ToggleOptIn
      :id="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`"
      v-model:has-opted-in="instructor.hasOptedIn"
      v-model:instructor-uid="instructor.uid"
      class="align-center mr-2 toggle-position"
    />
    <label :for="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`">
      <span
        :class="{'text-primary': instructor.optedInAt}"
        class="font-weight-bold instructor-label"
      >
        <span v-if="instructor.optedInAt">Click to opt out.</span>
        <span v-if="!instructor.optedInAt">Click to opt in.</span>
      </span>
    </label>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {find} from 'lodash'
import {storeToRefs} from 'pinia'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import ToggleOptIn from '@/components/course/ToggleOptIn.vue'

const {course} = storeToRefs(useCourseStore())
const instructor = computed(() => {
  const course = useCourseStore().course
  const uid = useContextStore().currentUser.uid
  const instructor = find(course.instructors, ['uid', uid])
  if (!instructor) {
    throw new Error(`No instructor found with UID ${uid}`)
  }
  return instructor
})
</script>

<style scoped>
.instructor-label {
  font-size: 19px;
}
</style>
