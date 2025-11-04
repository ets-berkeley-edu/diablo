<template>
  <div>
    <h3 v-if="course.instructors.length" id="instructors-header">
      <span aria-live="polite">
        <span v-if="course.hasOptedIn && course.scheduled">
          {{ course.instructors.length === 1 ? (course.instructors[0].uid === currentUser.uid ? 'You' : 'Instructor') : 'Instructors listed' }} will have editing and publishing access:
        </span>
      </span>
      <span v-if="!course.hasOptedIn || !course.scheduled">
        {{ pluralize('Instructor', course.instructors.length, false) }}
      </span>
    </h3>
    <h3 v-if="!course.instructors.length" id="instructors-header" class="font-size-16">
      No instructors are assigned to this course
    </h3>
    <CoursePageInstructorLabel
      v-for="instructor in instructorsSorted"
      :key="`instructor-${instructor.uid}`"
      :class="{'text-success': instructor.optedInAt, 'text-warning': !instructor.optedInAt}"
      class="ml-2"
      :instructor="instructor"
    />
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {sortBy} from 'lodash'
import {storeToRefs} from 'pinia'
import type {CourseInstructor} from '@/lib/types'
import {pluralize} from '@/lib/utils'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import CoursePageInstructorLabel from '@/components/course/CoursePageInstructorLabel.vue'

const {course} = storeToRefs(useCourseStore())
const currentUser = useContextStore().currentUser
const instructorsSorted = computed(() => {
  let instructors = sortBy(course.value.instructors, ['name'])
  if (!currentUser.isAdmin) {
    instructors = sortBy(course.value.instructors, (instructor: CourseInstructor) => (instructor.uid === currentUser.uid ? 0 : 1))
  }
  return instructors
})
</script>
