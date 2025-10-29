<template>
  <div v-if="!contextStore.loading" class="px-4 py-5">
    <v-card class="border-sm pr-12 px-6 py-3">
      <v-card-title class="py-0">
        <PageTitle :icon="mdiVideoPlus" :text="pageTitle" />
      </v-card-title>
      <v-card-subtitle class="pt-0 text-wrap">
        <div class="opt-in-banner mb-4" role="note" aria-label="Course Capture opt-in change notice">
          <span class="font-weight-bold">Course Capture has changed for 2026.</span>
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
        <div aria-labelledby="courses-table-eligible-header" class="border-sm pt-6 px-6 rounded" role="region">
          <h2 id="courses-table-eligible-header" class="text-medium-emphasis w-100">
            Courses eligible for capture
          </h2>
          <div v-if="!eligibleCourses.length" class="px-4 pt-2">No courses.</div>
          <HomeCoursesTable
            v-if="eligibleCourses.length"
            :courses="eligibleCourses"
            courses-type="eligible"
          />
        </div>
        <div v-if="ineligibleCourses.length" class="mb-2 mt-6" role="region">
          <v-expansion-panels class="border-sm rounded" flat rounded>
            <v-expansion-panel>
              <v-expansion-panel-title
                id="ineligible-courses-show-hide-btn"
                class="bg-primary"
                focusable
                hide-actions
              >
                <template #default="{expanded}">
                  <div class="align-center d-flex">
                    <div class="mr-2">
                      <v-icon
                        color="white"
                        :icon="expanded ? mdiMenuDown : mdiMenuRight"
                        size="x-large"
                      />
                    </div>
                    <div class="font-size-18">Courses not in a course capture classroom</div>
                  </div>
                </template>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <template #default>
                  <HomeCoursesTable :courses="ineligibleCourses" courses-type="ineligible" />
                </template>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </div>
      </v-card-text>
    </v-card>
    <v-card class="border-sm mt-8 pt-5 px-6">
      <v-card-title class="pb-0">
        <h2 class="font-size-24">Preferences</h2>
      </v-card-title>
      <v-card-text>
        <CourseCapturePreferences
          :disable-email-because-courses="eligibleCourses.some(c => c.hasOptedIn || isCourseScheduled(c))"
          :initial-do-not-email="currentUser.doNotEmail"
          :initial-opt-in-new-courses="currentUser.optInNewCourses"
          :uid="currentUser.uid"
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
import {getCourseCodes, getCourseStatusLabel, getDisplayMeetings, isCourseScheduled} from '@/lib/berkeley'
import {partitionCoursesByEligibility, pluralize} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const config = contextStore.config
const currentUser = contextStore.currentUser
const eligibleCourses = ref<Course[]>([])
const ineligibleCourses = ref<Course[]>([])
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
</script>

<style>
.opt-in-banner {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid #b3dcff;
  border-radius: 8px;
  padding: 12px 16px;
  line-height: 1.4;
}
.opt-in-banner-link {
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
