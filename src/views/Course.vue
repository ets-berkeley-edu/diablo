<template>
  <div v-if="!loading">
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
    <div v-if="isCurrentTerm && !!capability && hasValidMeetingTimes" class="px-4">
      <div aria-live="polite">
        <div v-if="course.scheduled">
          <v-alert
            v-if="updatesQueued"
            id="notice-queued"
            class="font-weight-bold"
            :icon="mdiAlert"
            type="warning"
            variant="outlined"
          >
            Recent updates to recording settings are currently queued for publication. They will be published in an hour or less.
          </v-alert>
          <div id="notice-scheduled" class="font-weight-bold text-success pa-6">
            {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture. The first recording is on
            <span class="text-no-wrap">
              <Date :date="course.scheduled[0].meetingStartDate" />.
            </span>
          </div>
        </div>
      </div>
      <div v-if="currentUser.isAdmin">
        <v-col>
          <ToggleOptIn
            :disabled="courseStore.disableButtons"
            :initial-value="course.hasOptedIn"
            :instructor-uids="['admin']"
            label="as admin"
            :on-toggle="onToggle"
            :section-id="`${course.sectionId}`"
            :term-id="`${course.termId}`"
          />
        </v-col>
      </div>
    </div>
    <v-row>
      <v-col
        cols="12"
        md="8"
        order="2"
        xl="9"
      >
        <v-card>
          <v-container v-if="isCurrentTerm && !!capability && hasValidMeetingTimes" class="pt-6">
            <DescribeCourseSchedulingStatus />
            <v-row
              align="center"
              aria-label="Instructors"
              justify="start"
              role="region"
            >
              <v-col id="instructors-list" class="px-4" cols="12">
                <h3 id="instructors-header">
                  <span v-if="course.scheduled">
                    <span :aria-hidden="true">Instructor(s)</span><span class="sr-only">Instructors</span> listed will have editing and publishing access:
                  </span>
                  <span v-if="!course.deletedAt && !course.scheduled">
                    <span :aria-hidden="true">Instructor(s):</span><span class="sr-only">Instructors</span>
                  </span>
                </h3>
                <div class="pl-4">
                  <div v-if="isEmpty(course.instructors)" class="mt-1 text-medium-emphasis">
                    No instructors
                  </div>
                  <div
                    v-for="instructor in course.instructors"
                    :id="`instructor-${instructor.uid}`"
                    :key="`instructor-${instructor.uid}`"
                    class="mt-1"
                  >
                    {{ instructor.name }} ({{ instructor.uid }})
                  </div>
                </div>
              </v-col>
            </v-row>
            <Collaborators
              v-if="!!capability"
              :set-model="collaborators => course.collaborators = collaborators"
            />
            <RecordingType
              v-if="!!capability"
              :set-model="setRecordingType"
            />
            <RecordingPlacement
              v-if="!!capability"
              :course="course"
              :set-model="setRecordingPlacement"
            />
            <v-row v-if="!currentUser.isAdmin && course.publishType">
              <v-col class="px-4">
                <hr>
                <KnowledgeBaseKalturaMyMedia v-if="course.publishType === 'kaltura_my_media'" class="mt-4" />
                <KnowledgeBaseKalturaMediaGallery v-if="course.publishType.startsWith('kaltura_media_gallery')" class="mt-4" />
              </v-col>
            </v-row>
            <div v-if="currentUser.isAdmin" class="my-3">
              <ScheduledCourse />
            </div>
          </v-container>
          <v-container v-if="isCurrentTerm && !capability" class="pt-6">
            <v-row>
              <v-col class="d-flex justify-start pl-7">
                <v-icon class="mr-2" color="error" :icon="mdiAlert" />
                <div id="course-not-eligible">
                  This course is not eligible for Course Capture because
                  <span v-if="location">{{ location }} is not capture-enabled.</span>
                  <span v-if="!location">it has no meeting location.</span>
                </div>
              </v-col>
            </v-row>
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
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {isEmpty} from 'lodash'
import {mdiAlert, mdiBookMultipleOutline} from '@mdi/js'
import {storeToRefs} from 'pinia'
import {useRoute} from 'vue-router'
import {getAuditoriums} from '@/api/room'
import {getCourse} from '@/api/course'
import {getCourseCodes, getTermName} from '@/lib/utils'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course.js'
import Collaborators from '@/components/course/Collaborators'
import CourseHistory from '@/components/course/CourseHistory'
import CourseNotes from '@/components/course/CourseNotes'
import CoursePageSidebar from '@/components/course/CoursePageSidebar'
import Date from '@/components/util/Date'
import PageTitle from '@/components/util/PageTitle'
import RecordingPlacement from '@/components/course/RecordingPlacement'
import RecordingType from '@/components/course/RecordingType'
import ScheduledCourse from '@/components/course/ScheduledCourse'
import ToggleOptIn from '@/components/course/ToggleOptIn.vue'
import KnowledgeBaseKalturaMyMedia from '@/components/course/KnowledgeBaseKalturaMyMedia.vue'
import KnowledgeBaseKalturaMediaGallery from '@/components/course/KnowledgeBaseKalturaMediaGallery.vue'
import DescribeCourseSchedulingStatus from '@/components/course/DescribeCourseSchedulingStatus.vue'

const contextStore = useContextStore()
const courseStore = useCourseStore()

const {course} = storeToRefs(courseStore)
const {config, currentUser, loading} = storeToRefs(contextStore)
const agreedToTerms = ref(false)
const auditoriums = ref([])
const capability = ref()
const courseDisplayTitle = ref('')
const hasValidMeetingTimes = ref(false)
const instructors = ref([])
const instructorProxies = ref([])
const location = ref('')

const isCurrentTerm = computed(() => course.value.termId === config.value.currentTermId)
const updatesQueued = computed(() => !!course.value.updateHistory.find(u => u.status === 'queued'))

contextStore.loadingStart('Course')

onMounted(() => {
  const {params} = useRoute()
  refreshCourse(params.termId, params.sectionId).then(() => {
    contextStore.loadingComplete(courseDisplayTitle.value)
  })
})

const refreshCourse = (termId, sectionId) => {
  return getCourse(termId, sectionId).then(data => {
    courseStore.setCourse(data)
    agreedToTerms.value = currentUser.isAdmin
    instructors.value = data.instructors.filter(i => i.roleCode !== 'APRX')
    instructorProxies.value = data.instructors.filter(i => i.roleCode === 'APRX')
    const eligible = data.meetings.eligible
    const meeting = eligible[0] || data.meetings.ineligible[0]
    capability.value = meeting.room?.capability
    location.value = meeting.room?.location
    hasValidMeetingTimes.value = eligible.some(m => m.startDate && m.startTime && m.endDate && m.endTime)
    courseDisplayTitle.value = getCourseCodes(data)[0]
    getAuditoriums().then(aud => {
      auditoriums.value = aud
    })
  })
}

const onToggle = () => {
  refreshCourse(course.value.termId, course.value.sectionId)
}

const setRecordingPlacement = updatedCourse => {
  course.value.canvasSiteIds = updatedCourse.canvasSiteIds
  course.value.canvasSites = updatedCourse.canvasSites
  course.value.publishType = updatedCourse.publishType
  course.value.publishTypeName = updatedCourse.publishTypeName
}

const setRecordingType = updatedCourse => {
  course.value.recordingType = updatedCourse.recordingType
  course.value.recordingTypeName = updatedCourse.recordingTypeName
}
</script>
