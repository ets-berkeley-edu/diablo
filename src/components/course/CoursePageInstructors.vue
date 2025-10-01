<template>
  <div id="instructors-list">
    <h3 v-if="course.instructors.length" id="instructors-header" class="font-size-16">
      <span v-if="course.scheduled">
        {{ course.instructors.length === 1 ? 'Instructor' : 'Instructors listed' }} will have editing and publishing access:
      </span>
      <span v-if="!course.deletedAt && !course.scheduled">
        Instructor{{ course.instructors.length === 1 ? '' : 's' }}
      </span>
    </h3>
    <h3 v-if="!course.instructors.length" class="font-size-16">
      No instructors are assigned to this course
    </h3>
    <div class="mt-3">
      <div v-if="!course.instructors.length" class="mt-1 text-medium-emphasis">
        <div v-if="currentUser.isAdmin">
          <ToggleOptIn
            :id="`toggle-opt-in-${course.termId}-${course.sectionId}`"
            v-model:has-opted-in="course.hasOptedIn"
          >
            {{ course.hasOptedIn ? 'This course is opted in to Course Capture' : 'This course is NOT opted in to Course Capture' }}
          </ToggleOptIn>
        </div>
        <div v-if="!currentUser.isAdmin">
          <!-- Non-admins should never reach a zero-instructor course page and yet we accommodate. -->
          No instructors
        </div>
      </div>
      <div
        v-for="instructor in instructorsSorted"
        :key="`instructor-${instructor.uid}`"
        class="d-flex flex-column"
      >
        <div v-if="!currentUser.isAdmin && currentUser.uid !== instructor.uid" class="font-size-18 mt-1">
          <CoursePageInstructorLabel
            :hide-opt-in-status="initialOptedInStatusByUID[instructor.uid] !== instructor.hasOptedIn"
            :instructor="instructor"
          />
        </div>
        <ToggleOptIn
          v-if="currentUser.isAdmin || currentUser.uid === instructor.uid"
          :id="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`"
          v-model:has-opted-in="instructor.hasOptedIn"
          v-model:instructor-uid="instructor.uid"
        >
          <CoursePageInstructorLabel
            :hide-opt-in-status="initialOptedInStatusByUID[instructor.uid] !== instructor.hasOptedIn"
            :instructor="instructor"
          />
        </ToggleOptIn>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {each, sortBy} from 'lodash'
import {storeToRefs} from 'pinia'
import type {CourseInstructor} from '@/lib/types'
import {useCourseStore} from '@/stores/course'
import {useContextStore} from '@/stores/context'
import CoursePageInstructorLabel from '@/components/course/CoursePageInstructorLabel.vue'
import ToggleOptIn from '@/components/course/ToggleOptIn.vue'

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const currentUser = useContextStore().currentUser
const instructorsSorted = ref<CourseInstructor[]>([])
const initialOptedInStatusByUID = ref({})

onMounted(() => {
  instructorsSorted.value = sortBy(course.value.instructors, ['name'])
  if (!currentUser.isAdmin) {
    instructorsSorted.value = sortBy(course.value.instructors, (instructor: CourseInstructor) => (instructor.uid === currentUser.uid ? 0 : 1))
  }
  each(course.value.instructors, instructor => {
    initialOptedInStatusByUID.value[instructor.uid] = instructor.hasOptedIn
  })
})
</script>
