<template>
  <div v-if="!contextStore.loading">
    <v-card class="border-sm pr-md-12 pl-md-6 py-3">
      <v-card-title class="py-0">
        <PageTitle :icon="mdiVideoPlus" :text="pageTitle" />
      </v-card-title>
      <v-card-subtitle class="pt-0 text-wrap">
        <div
          aria-label="Course Capture opt-in change notice"
          class="font-weight-bold mb-4 opt-in-banner text-black"
          role="note"
        >
          <span>Course Capture has changed for 2026.</span>
          You must opt in for your courses to be recorded. For more information, visit our
          <a
            :href="get(config, 'instructorGettingStartedUrl', 'https://rtl.berkeley.edu/services-programs/course-capture/instructor-getting-started')"
            target="_blank"
            rel="noopener"
            class="opt-in-banner-link"
          >
            Instructor Getting Started Guide<span class="sr-only">&nbsp;(opens in new tab)</span>
          </a>.
        </div>
      </v-card-subtitle>
      <v-card-text class="pt-0">
        <div
          aria-labelledby="courses-table-eligible-header"
          class="border-md mt-3 px-6 py-5 rounded"
          role="region"
        >
          <h2 id="courses-table-eligible-header" class="text-medium-emphasis w-100">
            Courses eligible for capture
          </h2>
          <div class="my-1">
            Click {{ eligibleCourses.length > 1 ? 'on each' : 'the' }} course link below to opt in and change course settings.
          </div>
          <div v-if="!eligibleCourses.length" class="pa-4">No courses.</div>
          <HomeCoursesTable
            v-if="eligibleCourses.length"
            :courses="eligibleCourses"
            courses-type="eligible"
          />
        </div>
        <div v-if="ineligibleCourses.length" class="border-md mb-2 mt-8 py-3 rounded" role="region">
          <div class="align-center d-flex ml-3">
            <div class="mr-4">
              <v-btn
                id="expand-ineligible-courses"
                aria-labelledby="expand-ineligible-courses-label"
                size="large"
                variant="text"
                @click="onClickShowIneligibleCourses"
              >
                <template #prepend>
                  <v-icon
                    color="primary"
                    :icon="isShowingIneligibleCourses ? mdiMenuDown : mdiMenuRight"
                    size="x-large"
                  />
                </template>
                <template #default>
                  <h2 class="expand-ineligible-courses-label font-size-18 text-medium-emphasis">
                    Courses not in a course capture classroom
                  </h2>
                </template>
              </v-btn>
            </div>
          </div>
          <v-expand-transition class="px-7">
            <div v-if="isShowingIneligibleCourses">
              <HomeCoursesTable :courses="ineligibleCourses" courses-type="ineligible" />
            </div>
          </v-expand-transition>
        </div>
      </v-card-text>
    </v-card>
    <v-card class="border-sm mt-8 pt-5 px-md-6">
      <v-card-title class="pb-0">
        <h2 class="font-size-24">Preferences</h2>
      </v-card-title>
      <v-card-text>
        <CourseCapturePreferences
          v-model="currentUser"
          :disable-email-because-courses="eligibleCourses.some(c => c.hasOptedIn || isCourseScheduled(c))"
          :on-update-user="onUpdateUser"
        />
      </v-card-text>
    </v-card>
  </div>
</template>

<script lang="ts" setup>
import {each, get, size} from 'lodash'
import {mdiMenuDown, mdiMenuRight, mdiVideoPlus} from '@mdi/js'
import {onMounted, ref} from 'vue'
import CourseCapturePreferences from '@/components/course/CourseCapturePreferences.vue'
import HomeCoursesTable from '@/components/util/HomeCoursesTable.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import type {Course} from '@/lib/types'
import {alertScreenReader, partitionCoursesByEligibility, pluralize} from '@/lib/utils'
import {getCourseCodes, getCourseStatusLabel, getDisplayMeetings, isCourseScheduled} from '@/lib/berkeley'
import {getCurrentUser} from '@/api/user'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const config = contextStore.config
const currentUser = contextStore.currentUser
const eligibleCourses = ref<Course[]>([])
const ineligibleCourses = ref<Course[]>([])
const isShowingIneligibleCourses = ref(false)
const pageTitle = ref('')

contextStore.loadingStart()

onMounted(() => {
  each(currentUser.courses, course => course.courseCodes = getCourseCodes(course))
  partitionCoursesByEligibility(currentUser.courses, eligibleCourses.value, ineligibleCourses.value)
  each([...eligibleCourses.value, ...ineligibleCourses.value], course => {
    course.displayMeetings = getDisplayMeetings(course)
    course.statusLabel = getCourseStatusLabel(course)
  })
  pageTitle.value = `Your ${config.currentTermName} ${pluralize('Course', size(currentUser.courses), false)}`
  contextStore.loadingComplete(pageTitle.value)
})

const onClickShowIneligibleCourses = () => {
  isShowingIneligibleCourses.value = !isShowingIneligibleCourses.value
  alertScreenReader(`Ineligible courses are now ${isShowingIneligibleCourses.value ? 'showing' : 'hidden'}.`)
}

const onUpdateUser = () => {
  getCurrentUser().then(contextStore.setCurrentUser)
}
</script>

<style>
.expand-ineligible-courses-label {
  letter-spacing: 0.25px;
  text-transform: none;
}
.opt-in-banner {
  line-height: 1.4;
}
.opt-in-banner-link {
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
