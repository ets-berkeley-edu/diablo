<template>
  <div v-if="currentUser.isAdmin" class="mt-2">
    <h3 v-if="course.instructors.length" id="instructors-header">
      <span v-if="course.hasOptedIn && course.scheduled">
        {{ course.instructors.length === 1 ? (course.instructors[0].uid === currentUser.uid ? 'You' : 'Instructor') : 'Instructors listed' }}
        will have editing and publishing access:
      </span>
      <span v-if="!course.hasOptedIn || !course.scheduled">
        Instructor{{ course.instructors.length === 1 ? '' : 's' }}
      </span>
    </h3>
    <h3 v-if="!course.instructors.length" id="instructors-header" class="font-size-16">
      No instructors are assigned to this course
    </h3>
    <div v-if="!course.instructors.length" class="mt-1 text-medium-emphasis">
      <ToggleOptIn
        :id="`toggle-opt-in-${course.termId}-${course.sectionId}`"
        v-model:has-opted-in="course.hasOptedIn"
        :label="course.hasOptedIn ? 'This course is opted in to Course Capture' : 'This course is NOT opted in to Course Capture'"
      />
    </div>
    <div
      v-for="instructor in instructorsSorted"
      :key="`instructor-${instructor.uid}`"
      class="align-center d-flex ml-2"
    >
      <ToggleOptIn
        :id="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`"
        v-model:has-opted-in="instructor.hasOptedIn"
        v-model:instructor-uid="instructor.uid"
        class="mr-2"
      />
      <CoursePageInstructorLabel :instructor="instructor" />
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {sortBy} from 'lodash'
import {storeToRefs} from 'pinia'
import type {CourseInstructor} from '@/lib/types'
import {useCourseStore} from '@/stores/course'
import {useContextStore} from '@/stores/context'
import CoursePageInstructorLabel from '@/components/course/CoursePageInstructorLabel.vue'
import ToggleOptIn from '@/components/course/ToggleOptIn.vue'

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const currentUser = useContextStore().currentUser
const instructorsSorted = computed(() => {
  let instructors = sortBy(course.value.instructors, ['name'])
  if (!currentUser.isAdmin) {
    instructors = sortBy(course.value.instructors, (instructor: CourseInstructor) => (instructor.uid === currentUser.uid ? 0 : 1))
  }
  return instructors
})
</script>
