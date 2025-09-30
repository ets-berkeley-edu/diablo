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
          <v-card class="pa-4">
            <DescribeCourseSchedulingStatus />
            <v-container v-if="isEligibleForCourseCapture" class="pt-0">
              <CoursePageInstructors class="mt-3" />
              <Collaborators v-model="course.collaborators" />
              <RecordingType v-model="course.recordingType" />
              <RecordingPlacement
                v-model:canvas-site-ids="course.canvasSiteIds"
                v-model:publish-type="course.publishType"
              />
              <v-row>
                <v-col class="pb-5 pl-4 pt-1">
                  <ProgressButton
                    id="btn-publish-type-save"
                    :action="save"
                    aria-label="Save Recording Placement"
                    :disabled="isSaving"
                    :in-progress="isSaving"
                    :text="isSaving ? 'Saving' : 'Save'"
                  />
                  <v-btn
                    id="btn-publish-type-cancel"
                    aria-label="Cancel Recording Placement Edit"
                    class="ml-1"
                    :disabled="isSaving"
                    text="Cancel"
                    variant="text"
                    @click="reset"
                  />
                </v-col>
              </v-row>
              <v-row v-if="!currentUser.isAdmin && course.publishType" class="mt-0">
                <v-col>
                  <hr>
                  <KnowledgeBaseKalturaMyMedia v-if="course.publishType === 'kaltura_my_media'" class="mt-4" />
                  <KnowledgeBaseKalturaMediaGallery v-if="course.publishType.startsWith('kaltura_media_gallery')" class="mt-4" />
                </v-col>
              </v-row>
              <div v-if="currentUser.isAdmin" class="my-3">
                <ScheduledCourse />
              </div>
            </v-container>
            <v-container v-if="isCurrentTerm && !!capability && !hasValidMeetingTimes" class="pt-6">
              <v-row>
                <v-col class="d-flex justify-start">
                  <v-icon class="mr-2" color="error" :icon="mdiAlert" />
                  <div id="invalid-meeting-times">
                    This course is in a capture-enabled room but the meeting times are missing or invalid.
                  </div>
                </v-col>
              </v-row>
            </v-container>
            <v-container v-if="!isCurrentTerm" class="pt-6">
              <v-row>
                <v-col class="d-flex justify-start">
                  <v-icon class="mr-2" color="error" :icon="mdiAlert" />
                  <div id="course-not-current">
                    This course is not currently eligible for Course Capture.
                  </div>
                </v-col>
              </v-row>
            </v-container>
          </v-card>
        </v-col>
        <v-col
          cols="12"
          md="4"
          order="1"
          xl="3"
        >
          <CoursePageSidebar :course="course" />
          <CourseNotes :course="course" :set-model="note => course.note = note" />
        </v-col>
      </v-row>
      <v-row v-if="currentUser.isAdmin">
        <v-col cols="12">
          <CourseHistory :history="course.updateHistory" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {mdiAlert, mdiBookMultipleOutline} from '@mdi/js'
import {useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {getCourseCodes, getTermName} from '@/lib/berkeley'
import {getCourse, updateCourse} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import Collaborators from '@/components/course/Collaborators.vue'
import CourseHistory from '@/components/course/CourseHistory.vue'
import CourseNotes from '@/components/course/CourseNotes.vue'
import CoursePageInstructors from '@/components/course/CoursePageInstructors.vue'
import CoursePageSidebar from '@/components/course/CoursePageSidebar.vue'
import DescribeCourseSchedulingStatus from '@/components/course/DescribeCourseSchedulingStatus.vue'
import KnowledgeBaseKalturaMyMedia from '@/components/course/KnowledgeBaseKalturaMyMedia.vue'
import KnowledgeBaseKalturaMediaGallery from '@/components/course/KnowledgeBaseKalturaMediaGallery.vue'
import PageTitle from '@/components/util/PageTitle.vue'
import ProgressButton from '@/components/util/ProgressButton.vue'
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
const isSaving = ref(false)
const sectionId = ref()
const termId = ref()

contextStore.loadingStart('Course')

onMounted(() => {
  const {params} = useRoute()
  sectionId.value = params.sectionId
  termId.value = params.termId
  reset()
})

const reset = () => {
  getCourse(termId.value, sectionId.value).then(data => {
    courseStore.setCourse(data)
    agreedToTerms.value = currentUser.isAdmin
    courseDisplayTitle.value = getCourseCodes(data)[0]
    contextStore.loadingComplete(courseDisplayTitle.value)
  })
}

const save = () => {
  isSaving.value = true
  updateCourse(course.value).then(data => {
    course.value = data
    isSaving.value = false
  })
}
</script>
