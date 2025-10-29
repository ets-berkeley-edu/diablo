<template>
  <v-card
    v-if="!contextStore.loading"
    class="border-sm px-6"
  >
    <v-card-title>
      <PageTitle
        :icon="mdiVideoPlus"
        :text="pageTitle"
      />
    </v-card-title>
    <v-card-text>
      <Spinner v-if="refreshingCourses" />
      <template v-if="!refreshingCourses">
        <div class="opt-in-banner mb-4" role="note" aria-label="Course Capture opt-in change notice">
          <p class="m-0">
            <strong>Course Capture has changed for 2026.</strong>
            You must opt in for your courses to be recorded.
            For more information, visit our
            <a
              :href="gettingStartedUrl"
              target="_blank"
              rel="noopener"
              class="opt-in-banner__link"
            >
              Instructor Getting Started Guide<span class="sr-only">&nbsp;(opens in new tab)</span>
            </a>.
          </p>
        </div>
        <HomeCoursesEligible :courses="eligibleCourses" />
        <HomeCoursesNotEligible :courses="eligibleCourses" />
      </template>
      <v-divider class="my-12" />
      <CourseCapturePreferences
        :disable-email-because-courses="anyCourseOptedInOrScheduled"
        :initial-do-not-email="currentUser.doNotEmail"
        :initial-opt-in-new-courses="currentUser.optInNewCourses"
        :uid="currentUser.uid"
      />
    </v-card-text>
  </v-card>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {each, get, size} from 'lodash'
import {mdiVideoPlus} from '@mdi/js'
import {storeToRefs} from 'pinia'
import CourseCapturePreferences from '@/components/course/CourseCapturePreferences.vue'
import HomeCoursesEligible from '@/components/util/HomeCoursesEligible.vue'
import HomeCoursesNotEligible from '@/components/util/HomeCoursesNotEligible.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import Spinner from '@/components/util/Spinner.vue'
import type {Course} from '@/lib/types'
import {getCourseCodes, getCourseStatusLabel, getDisplayMeetings, isCourseScheduled} from '@/lib/berkeley'
import {partitionCoursesByEligibility, pluralize} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const {config, currentUser} = storeToRefs(contextStore)
const eligibleCourses = ref<Course[]>([])
const ineligibleCourses = ref<Course[]>([])
const pageTitle = ref('')
const refreshingCourses = ref(false)

const anyCourseOptedInOrScheduled = computed(() => {
  return [...eligibleCourses.value] .some(c => c.hasOptedIn || isCourseScheduled(c))
})

const gettingStartedUrl = computed(() =>
  get(config.value, 'instructorGettingStartedUrl', 'https://rtl.berkeley.edu/services-programs/course-capture/instructor-getting-started')
)

contextStore.loadingStart()

onMounted(() => {
  refreshCourses()
  pageTitle.value = `Your ${config.value.currentTermName} ${pluralize('Course', size(currentUser.value.courses), false)}`
  contextStore.loadingComplete(pageTitle.value)
})

const refreshCourses = () => {
  each(currentUser.value.courses, course => {
    course.courseCodes = getCourseCodes(course)
  })

  eligibleCourses.value = []
  ineligibleCourses.value = []
  partitionCoursesByEligibility(currentUser.value.courses, eligibleCourses.value, ineligibleCourses.value)

  each([...eligibleCourses.value, ...ineligibleCourses.value], course => {
    course.displayMeetings = getDisplayMeetings(course)
    course.statusLabel = getCourseStatusLabel(course)
  })
}
</script>

<style>
.instructor-courses .v-table__wrapper {
  overflow: visible !important;
}
.v-selection-control--disabled .v-label {
  opacity: 0.6;
}
.opt-in-banner {
  background-color: rgb(var(--v-theme-surface));          /* light blue */
  border: 1px solid #b3dcff;     /* subtle blue border */
  border-radius: 8px;            /* slightly rounded edges */
  padding: 12px 16px;
  line-height: 1.4;
  width: 1200px;
}

.opt-in-banner__link {
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
