<template>
  <div id="instructors-list">
    <h3 v-if="course.instructors.length" id="instructors-header">
      <span v-if="course.hasOptedIn && course.scheduled">
        {{ course.instructors.length === 1 ? (course.instructors[0].uid === currentUser.uid ? 'You' : 'Instructor') : 'Instructors listed' }} will have editing and publishing access:
      </span>
      <span v-if="!course.hasOptedIn || !course.scheduled">
        Instructor{{ course.instructors.length === 1 ? '' : 's' }}
      </span>
    </h3>
    <h3 v-if="!course.instructors.length" id="instructors-header" class="font-size-16">
      No instructors are assigned to this course
    </h3>
    <div class="mt-2">
      <div v-if="!course.instructors.length" class="mt-1 text-medium-emphasis">
        <div v-if="currentUser.isAdmin && !course.deletedAt">
          <ToggleOptIn
            :id="`toggle-opt-in-${course.termId}-${course.sectionId}`"
            v-model:has-opted-in="course.hasOptedIn"
            :label="course.hasOptedIn ? 'This course is opted in to Course Capture' : 'This course is NOT opted in to Course Capture'"
          />
        </div>
        <div v-if="!currentUser.isAdmin">
          <!-- Non-admins should never reach a zero-instructor course page and yet we accommodate. -->
          No instructors
        </div>
      </div>
      <div
        v-for="(instructor, index) in instructorsSorted"
        :key="`instructor-${instructor.uid}`"
        class="d-flex flex-column ml-2"
      >
        <div
          v-if="!currentUser.isAdmin && currentUser.uid !== instructor.uid && !course.deletedAt"
          :class="index === 0 ? 'mt-0' : 'mt-2'"
          class="font-size-18"
        >
          <CoursePageInstructorLabel
            :hide-opt-in-status="initialOptedInStatusByUID[instructor.uid] !== instructor.hasOptedIn"
            :instructor="instructor"
          />
        </div>
        <div v-if="(currentUser.isAdmin || currentUser.uid === instructor.uid) && !course.deletedAt" class="d-flex align-center flex-wrap gap-2">
          <label
            v-if="!currentUser.isAdmin"
            class="align-center d-flex current-instructor"
            :for="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`"
          >
            <ToggleOptIn
              :id="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`"
              v-model:has-opted-in="instructor.hasOptedIn"
              v-model:instructor-uid="instructor.uid"
              class="align-center mr-2 toggle-position"
            />
            <div class="mr-2">
              {{ instructor.name }}
            </div>
            <div v-if="currentUser.uid === instructor.uid">
              <span v-if="instructor.optedInAt" class="text-success">(opted in {{ DateTime.fromISO(instructor.optedInAt).toRelativeCalendar({}) }})</span>
              <span v-if="!instructor.optedInAt" class="text-warning">(not yet opted in)</span>
            </div>
          </label>
          <div v-if="currentUser.isAdmin" class="align-center d-flex">
            <ToggleOptIn
              :id="`toggle-opt-in-${course.termId}-${course.sectionId}-instructor-${instructor.uid}`"
              v-model:has-opted-in="instructor.hasOptedIn"
              v-model:instructor-uid="instructor.uid"
              class="align-center d-inline-flex mr-2"
            />
            <div class="instructor-label">
              <CoursePageInstructorLabel
                :hide-opt-in-status="initialOptedInStatusByUID[instructor.uid] !== instructor.hasOptedIn"
                :instructor="instructor"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {DateTime} from 'luxon'
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
const instructorsSorted = computed(() => {
  let instructors = sortBy(course.value.instructors, ['name'])
  if (!currentUser.isAdmin) {
    instructors = sortBy(course.value.instructors, (instructor: CourseInstructor) => (instructor.uid === currentUser.uid ? 0 : 1))
  }
  return instructors
})
const initialOptedInStatusByUID = ref({})

onMounted(() => {
  each(course.value.instructors, instructor => {
    initialOptedInStatusByUID.value[instructor.uid] = instructor.hasOptedIn
  })
})
</script>

<style scoped>
.current-instructor {
  font-size: 18px;
}
.instructor-label {
  font-size: 19px;
}
</style>
