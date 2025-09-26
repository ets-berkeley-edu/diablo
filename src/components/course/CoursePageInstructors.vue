<template>
  <v-row
    align="center"
    aria-label="Instructors"
    justify="start"
    role="region"
  >
    <v-col id="instructors-list" class="pt-0" cols="12">
      <h3 id="instructors-header">
        <span v-if="course.scheduled">
          {{ course.instructors.length === 1 ? 'Instructor' : 'Instructors listed' }} will have editing and publishing access:
        </span>
        <span v-if="!course.deletedAt && !course.scheduled">
          Instructor{{ course.instructors.length === 1 ? '' : 's' }}
        </span>
      </h3>
      <div class="mt-1 pl-4">
        <div v-if="isEmpty(course.instructors)" class="mt-1 text-medium-emphasis">
          No instructors
        </div>
        <div
          v-for="instructor in instructorsSorted"
          :key="`instructor-${instructor.uid}`"
          class="d-flex flex-column"
        >
          <div v-if="!currentUser.isAdmin && currentUser.uid !== instructor.uid" class="font-size-18 mt-1">
            <CoursePageInstructorLabel :instructor="instructor" />
          </div>
          <ToggleOptIn
            v-if="currentUser.isAdmin || currentUser.uid === instructor.uid"
            :id="`instructor-${instructor.uid}`"
            v-model="instructor.hasOptedIn"
            :disabled="courseStore.disableButtons"
            :section-id="`${course.sectionId}`"
            :term-id="`${course.termId}`"
          >
            <CoursePageInstructorLabel :instructor="instructor" />
          </ToggleOptIn>
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import {isEmpty, sortBy} from 'lodash'
import {onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import type {CourseInstructor} from '@/lib/types'
import {useCourseStore} from '@/stores/course'
import {useContextStore} from '@/stores/context'
import ToggleOptIn from '@/components/course/ToggleOptIn.vue'
import CoursePageInstructorLabel from '@/components/course/CoursePageInstructorLabel.vue'

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const currentUser = useContextStore().currentUser
const instructorsSorted = ref<CourseInstructor[]>([])

onMounted(() => {
  instructorsSorted.value = sortBy(course.value.instructors, ['name'])
  if (!currentUser.isAdmin) {
    instructorsSorted.value = sortBy(course.value.instructors, (instructor: CourseInstructor) => (instructor.uid === currentUser.uid ? 0 : 1))
  }
})
</script>
