<template>
  <div class="font-weight-bold">
    <div v-if="isCurrentTerm && !capability" class="align-start d-flex py-2">
      <v-icon class="mr-3 mt-1" color="error" :icon="mdiAlert" />
      <div id="course-not-eligible">
        This course is not eligible for Course Capture because
        <span v-if="location">{{ location }} is not capture-enabled.</span>
        <span v-if="!location">it has no meeting location.</span>
      </div>
    </div>
    <v-expand-transition>
      <div v-if="isEligibleForCourseCapture && course.hasOptedIn && course.scheduled" aria-live="polite">
        <v-alert
          v-if="courseStore.updatesQueued"
          id="notice-queued"
          class="font-weight-bold"
          density="compact"
          :icon="mdiAlert"
          text="Recent updates to recording settings are queued to go live. They will be in effect within an hour."
          type="warning"
          variant="outlined"
        />
        <div id="notice-scheduled" class="font-weight-bold text-success mt-3">
          This course is scheduled for Course Capture. The first recording is on
          <span class="text-no-wrap">
            <Date :date="course.scheduled[0].meetingStartDate" />.
          </span>
        </div>
      </div>
    </v-expand-transition>
    <div v-if="isEligibleForCourseCapture && !course.deletedAt">
      <Alert
        v-if="!course.scheduled && !course.hasOptedIn && instructors.length"
        id="notice-opt-out"
        class="py-2"
        text="This course is not scheduled for Course Capture because at least one instructor is not opted in."
      />
      <Alert
        v-if="course.scheduled && !course.hasOptedIn && instructors.length"
        id="notice-opt-out-pending-instructors"
        class="py-2"
      >
        {{ currentUser.isAdmin ? 'This' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled shortly because
        {{ instructors.length === 1 && currentUser.uid === instructors[0].uid ? 'you have' : `${instructorsNotOptedInNames} ${instructorsNotOptedIn.length === 1 ? 'has ' : 'have'}` }}
        not opted in. To keep recordings scheduled, please have all instructors remove their opt-out status.
      </Alert>
      <Alert
        v-if="course.scheduled && !course.hasOptedIn && !instructors.length"
        id="notice-opt-out-pending-no-instructors"
        class="py-2"
      >
        {{ currentUser.isAdmin ? 'This' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled
        shortly due to an admin override. Please contact
        <a
          id="course-page-diablo-support-mailto"
          :href="`mailto:${config.emailCourseCaptureSupport}`"
          target="_blank"
        >
          {{ config.emailCourseCaptureSupport }}
        </a>
        if you have any questions.
      </Alert>
      <Alert
        v-if="!course.scheduled && course.hasOptedIn && instructors.length"
        id="notice-eligible-not-scheduled"
        class="py-2"
        text="Scheduling for this course is pending. This process will complete within an hour. Instructors will be notified when scheduling takes place."
        text-class="text-success"
      />
      <Alert
        v-if="!course.scheduled && !instructors.length && course.optIns.length === 1 && course.optIns[0].instructorUid === 'admin'"
        id="notice-eligible-scheduled-by-admin"
        class="py-2"
        text-class="text-success"
      >
        This course was scheduled for Course Capture by an Admin on {{ DateTime.fromISO(course.optIns[0].createdAt).toLocaleString(DateTime.DATE_MED) }}.
      </Alert>
      <Alert
        v-if="!course.scheduled && !instructors.length && !course.optIns.length"
        id="notice-eligible-not-scheduled"
        class="py-2"
        text="This course is eligible for Course Capture but has not been scheduled because it has no instructors."
        text-class="text-success"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {DateTime} from 'luxon'
import {filter, map} from 'lodash'
import {mdiAlert} from '@mdi/js'
import {ref} from 'vue'
import {storeToRefs} from 'pinia'
import {oxfordJoin} from '@/lib/utils'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import Alert from '@/components/util/Alert.vue'
import Date from '@/components/util/Date.vue'

const courseStore = useCourseStore()
const {
  capability,
  course,
  isCurrentTerm,
  isEligibleForCourseCapture,
  location
} = storeToRefs(courseStore)
const {config, currentUser} = storeToRefs(useContextStore())
const instructors = course.value.instructors
const instructorsNotOptedIn = ref(filter(instructors, ['hasOptedIn', false]))
const instructorsNotOptedInNames = oxfordJoin(map(instructorsNotOptedIn.value, 'name'))
</script>
