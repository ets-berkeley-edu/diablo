<template>
  <div v-if="!contextStore.loading">
    <PageTitle
      class="pl-4"
      :class-for-h1="course.deletedAt ? 'line-through' : ''"
      :icon="mdiBookMultipleOutline"
      :text="config.currentTermId === course.termId ? courseDisplayTitle : `${courseDisplayTitle} (${getTermName(course.termId)})`"
    />
    <div class="pl-16">
      <span v-if="course.deletedAt" class="text-subtitle-1">
        <span class="font-weight-bold text-error">UC Berkeley has canceled this section.</span>
      </span>
      <h2 v-if="!course.deletedAt" id="course-title" class="text-primary">{{ course.courseTitle }}</h2>
      <div class="text-body-1">
        Section ID: <span id="section-id">{{ course.sectionId }}</span>
      </div>
    </div>
    <v-container fluid>
      <v-row>
        <v-col
          cols="12"
          md="8"
          order="2"
          xl="9"
        >
          <v-card class="pb-6 pt-4 px-8">
            <DescribeCourseSchedulingStatus />
            <CoursePageInstructors class="mt-2" />
          </v-card>
          <v-card class="mt-8 px-4 py-3">
            <v-container v-if="isEligibleForCourseCapture">
              <Collaborators />
              <RecordingType v-model="course.recordingType" />
              <RecordingPlacement
                v-model:canvas-site-ids="course.canvasSiteIds"
                v-model:publish-type="course.publishType"
              />
              <v-row v-if="!currentUser.isAdmin && course.publishType" class="mt-0">
                <v-col>
                  <hr>
                  <KnowledgeBaseKalturaMyMedia v-if="course.publishType === 'kaltura_my_media'" class="mt-4" />
                  <KnowledgeBaseKalturaMediaGallery v-if="course.publishType.startsWith('kaltura_media_gallery')" class="mt-4" />
                </v-col>
              </v-row>
            </v-container>
            <div v-if="isCurrentTerm && !!capability && !hasValidMeetingTimes" class="align-start d-flex mt-4">
              <v-icon class="mr-3 mt-1" color="error" :icon="mdiAlert" />
              <div id="invalid-meeting-times">
                This course is in a capture-enabled room but the meeting times are missing or invalid.
              </div>
            </div>
            <div v-if="!isCurrentTerm" class="align-start d-flex mt-4">
              <v-icon class="mr-3 mt-1" color="error" :icon="mdiAlert" />
              <div id="course-not-current">
                This course is not currently eligible for Course Capture.
              </div>
            </div>
          </v-card>
          <v-card v-if="currentUser.isAdmin" class="mt-8 px-4 py-6">
            <ScheduledCourse />
          </v-card>
        </v-col>
        <v-col
          cols="12"
          md="4"
          order="1"
          xl="3"
        >
          <CoursePageSidebar :course="course" />
        </v-col>
      </v-row>
      <v-row v-if="currentUser.isAdmin">
        <v-col cols="12">
          <CourseHistory class="mt-4" :history="course.updateHistory" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {mdiAlert, mdiBookMultipleOutline} from '@mdi/js'
import {storeToRefs} from 'pinia'
import {toInteger} from 'lodash'
import {useRoute} from 'vue-router'
import {getCourseCodes, getTermName} from '@/lib/berkeley'
import {getCourse} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import Collaborators from '@/components/course/Collaborators.vue'
import CourseHistory from '@/components/course/CourseHistory.vue'
import CoursePageInstructors from '@/components/course/CoursePageInstructors.vue'
import CoursePageSidebar from '@/components/course/CoursePageSidebar.vue'
import DescribeCourseSchedulingStatus from '@/components/course/DescribeCourseSchedulingStatus.vue'
import KnowledgeBaseKalturaMyMedia from '@/components/course/KnowledgeBaseKalturaMyMedia.vue'
import KnowledgeBaseKalturaMediaGallery from '@/components/course/KnowledgeBaseKalturaMediaGallery.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import RecordingPlacement from '@/components/course/RecordingPlacement.vue'
import RecordingType from '@/components/course/RecordingType.vue'
import ScheduledCourse from '@/components/course/ScheduledCourse.vue'

const contextStore = useContextStore()
const courseStore = useCourseStore()

const {
  capability,
  course,
  hasValidMeetingTimes,
  isCurrentTerm,
  isEligibleForCourseCapture
} = storeToRefs(courseStore)
const config = contextStore.config
const agreedToTerms = ref(false)
const currentUser = contextStore.currentUser
const courseDisplayTitle = ref('')

contextStore.loadingStart('Course')

onMounted(() => {
  const {params} = useRoute()
  getCourse(toInteger(params.termId), toInteger(params.sectionId)).then(data => {
    courseStore.setCourse(data)
    agreedToTerms.value = currentUser.isAdmin
    courseDisplayTitle.value = getCourseCodes(data)[0]
    contextStore.loadingComplete(courseDisplayTitle.value)
    courseStore.setDisableButtons(false)
  })
})
</script>
