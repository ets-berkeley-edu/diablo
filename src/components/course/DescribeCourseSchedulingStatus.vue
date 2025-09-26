<template>
  <v-row class="mt-0">
    <v-col class="font-weight-bold">
      <div v-if="isEligibleForCourseCapture && course.hasOptedIn && course.scheduled" aria-live="polite">
        <v-alert
          v-if="courseStore.updatesQueued"
          id="notice-queued"
          class="font-weight-bold"
          density="compact"
          :icon="mdiAlert"
          text="Recent updates to recording settings are currently queued to go live. They will be activated within an hour."
          type="warning"
          variant="outlined"
        />
        <div id="notice-scheduled" class="font-weight-bold text-success mt-3">
          {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture. The first recording is on
          <span class="text-no-wrap">
            <Date :date="course.scheduled[0].meetingStartDate" />.
          </span>
        </div>
      </div>
      <div v-if="!course.deletedAt && !course.scheduled">
        <span v-if="!course.hasOptedIn && course.instructors.length" id="notice-opt-out" class="text-error">
          {{ currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture because one or more
          instructors have not opted in. To schedule recordings, please have all instructors opt-in.
        </span>
        <!--
        -------------------------------------------
        TODO: How and when do we show this message?
        -------------------------------------------
        <span v-if="!course.hasOptedIn && !course.scheduled && !course.instructors.length" id="notice-opt-out" class="text-error">
          {{ currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture due to an admin override.
          Please contact
          <a
            id="course-page-diablo-support-mailto"
            :href="`mailto:${config.emailCourseCaptureSupport}`"
            target="_blank"
          >
            {{ config.emailCourseCaptureSupport }}
          </a>.
        </span>
        -->
        <span v-if="course.scheduled && !course.hasOptedIn && course.instructors.length" id="notice-opt-out-pending-instructors" class="text-error">
          {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled
          shortly because one or more instructors have not opted in. To keep recordings scheduled, please have all
          instructors remove their opt-out status.
        </span>
        <span v-if="course.scheduled && !course.hasOptedIn && !course.instructors.length" id="notice-opt-out-pending-no-instructors" class="text-error">
          {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled
          shortly due to an admin override. Please contact
          <a
            id="course-page-diablo-support-mailto"
            :href="`mailto:${config.emailCourseCaptureSupport}`"
            target="_blank"
          >
            {{ config.emailCourseCaptureSupport }}
          </a>
          if you have any questions.
        </span>
        <span v-if="course.hasOptedIn && course.instructors.length" id="notice-eligible-not-scheduled" class="text-success">
          This course is eligible for scheduling, but has not yet been scheduled. Instructors will be notified when
          scheduling has taken place.
        </span>
        <span v-if="!course.instructors.length" class="text-success">
          <span
            v-if="course.optIns.length === 1 && course.optIns[0].instructorUid === 'admin'"
            id="notice-eligible-scheduled-by-admin"
          >
            This course was scheduled for Course Capture by an Admin on {{ DateTime.fromISO(course.optIns[0].createdAt).toLocaleString(DateTime.DATE_MED) }}.
          </span>
          <span v-if="!course.optIns.length" id="notice-eligible-not-scheduled">
            This course is eligible for Course Capture but has not been scheduled because it has no instructors.
          </span>
        </span>
      </div>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import {DateTime} from 'luxon'
import {mdiAlert} from '@mdi/js'
import {storeToRefs} from 'pinia'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import Date from '@/components/util/Date.vue'

const courseStore = useCourseStore()
const {course, isEligibleForCourseCapture} = storeToRefs(courseStore)
const {config, currentUser} = storeToRefs(useContextStore())
</script>
