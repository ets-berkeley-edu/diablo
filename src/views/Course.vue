<template>
  <div v-if="!loading">
    <PageTitle
      class="pl-4"
      :class-for-h1="course.deletedAt ? 'line-through' : ''"
      :icon="mdiBookMultipleOutline"
      :text="config.currentTermId === course.termId ? courseDisplayTitle : `${courseDisplayTitle} (${getTermName(course.termId)})`"
    />
    <div class="pl-16 pb-4">
      <span v-if="course.deletedAt" class="text-subtitle-1">
        <span class="font-weight-bold text-error">UC Berkeley has canceled this section.</span>
      </span>
      <h2 v-if="!course.deletedAt" id="course-title" class="text-primary">{{ course.courseTitle }}</h2>
      <div class="text-body-1">
        Section ID: <span id="section-id">{{ course.sectionId }}</span>
      </div>
    </div>
    <div v-if="isCurrentTerm && !!capability && hasValidMeetingTimes" class="pa-4">
      <div aria-live="polite">
        <div v-if="!course.hasOptedOut && course.scheduled">
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
        <div v-if="!course.deletedAt && (course.hasOptedOut || !course.scheduled)">
          <v-col class="font-weight-bold mb-1">
            <span v-if="course.hasOptedOut && !course.scheduled && course.instructors.length" id="notice-opt-out" class="text-error">
              {{ currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture because one or more instructors have opted out. To schedule recordings, please have all instructors remove their opt-out status.
            </span>
            <span v-if="course.hasOptedOut && !course.scheduled && !course.instructors.length" id="notice-opt-out" class="text-error">
              {{ currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture due to an admin override. Please contact
              <a
                id="course-page-diablo-support-mailto"
                :href="`mailto:${config.emailCourseCaptureSupport}`"
                target="_blank"
              >
                {{ config.emailCourseCaptureSupport }}
              </a>.
            </span>
            <span v-if="course.scheduled && course.hasOptedOut && course.instructors.length" id="notice-opt-out-pending-instructors" class="text-error">
              {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled shortly because one or more instructors have opted out. To keep recordings scheduled, please have all instructors remove their opt-out status.
            </span>
            <span v-if="course.scheduled && course.hasOptedOut && !course.instructors.length" id="notice-opt-out-pending-no-instructors" class="text-error">
              {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled shortly due to an admin override. Please contact
              <a
                id="course-page-diablo-support-mailto"
                :href="`mailto:${config.emailCourseCaptureSupport}`"
                target="_blank"
              >
                {{ config.emailCourseCaptureSupport }}
              </a>
              if you have any questions.
            </span>
            <span v-if="!course.scheduled && !course.hasOptedOut && course.instructors.length" id="notice-eligible-not-scheduled" class="text-success">
              This course is eligible for scheduling, but has not yet been scheduled. Instructors will be notified when scheduling has taken place.
            </span>
            <span v-if="!course.scheduled && !course.hasOptedOut && !course.instructors.length" id="notice-eligible-not-scheduled" class="text-success">
              This course is eligible for scheduling, but has not been scheduled because it has no instructors.
            </span>
          </v-col>
        </div>
      </div>
      <div v-if="currentUser.isAdmin">
        <v-col>
          <ToggleOptOut
            :term-id="`${course.termId}`"
            :section-id="`${course.sectionId}`"
            instructor-uid="admin"
            label="as admin"
            :initial-value="course.hasOptedOut"
            :on-toggle="onToggle"
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
            <v-row
              align="center"
              aria-label="Instructors"
              justify="start"
              role="region"
            >
              <v-col id="instructors-list" class="px-4 mb-2" cols="12">
                <h3 id="instructors-header">
                  <span v-if="!course.hasOptedOut && course.scheduled">
                    <span :aria-hidden="true">Instructor(s)</span><span class="sr-only">Instructors</span> listed will have editing and publishing access:
                  </span>
                  <span v-if="!course.deletedAt && (course.hasOptedOut || !course.scheduled)">
                    <span :aria-hidden="true">Instructor(s):</span><span class="sr-only">Instructors</span>
                  </span>
                </h3>
                <div v-if="isEmpty(course.instructors)" class="pl-4 pt-2 text-medium-emphasis">
                  No instructors
                </div>
                <div
                  v-for="instructor in course.instructors"
                  :id="`instructor-${instructor.uid}`"
                  :key="`instructor-${instructor.uid}`"
                  class="pl-4 pt-2"
                >
                  {{ instructor.name }} ({{ instructor.uid }})
                  <span v-if="instructor.hasOptedOut" :id="`instructor-${instructor.uid}-opt-out`">
                    (opted out)
                  </span>
                </div>
              </v-col>
            </v-row>
            <Collaborators
              v-if="!course.hasOptedOut && course.scheduled"
              :course="course"
              :set-model="collaborators => course.collaborators = collaborators"
            />
            <RecordingType
              v-if="!course.hasOptedOut && course.scheduled"
              :course="course"
              :labels="displayLabels"
              :set-model="setRecordingType"
            />
            <RecordingPlacement
              v-if="!course.hasOptedOut && course.scheduled"
              :course="course"
              :labels="displayLabels"
              :set-model="setRecordingPlacement"
            />
            <v-row v-if="!currentUser.isAdmin && get(course, 'publishType', '') === 'kaltura_my_media'">
              <v-col class="pa-4 my-2">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li>
                    <ExternalLink
                      href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013882"
                      :icon-size="16"
                      link-id="link-publish-my-media"
                    >
                      How to Publish from My Media
                    </ExternalLink>
                  </li>
                  <li>
                    <ExternalLink
                      href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013623"
                      :icon-size="16"
                      link-id="link-embed-rich-content"
                    >
                      How to Embed in bCourses using the Rich Content Editor
                    </ExternalLink>
                  </li>
                  <li>
                    <ExternalLink
                      href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115"
                      :icon-size="16"
                      link-id="link-download-second-stream"
                    >
                      How to Download the Second Stream of the Recording
                    </ExternalLink>
                  </li>
                  <li>
                    <ExternalLink
                      href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq"
                      :icon-size="16"
                      link-id="link-faq"
                    >
                      Course Capture FAQ
                    </ExternalLink>
                  </li>
                </ul>
              </v-col>
            </v-row>
            <v-row v-if="!currentUser.isAdmin && get(course, 'publishType', '').startsWith('kaltura_media_gallery')">
              <v-col class="pa-4 my-2">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li>
                    <ExternalLink
                      href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014032"
                      :icon-size="16"
                      link-id="link-remove-recording"
                    >
                      How to Remove a Recording from the Media Gallery
                    </ExternalLink>
                  </li>
                  <li>
                    <ExternalLink
                      href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115"
                      :icon-size="16"
                      link-id="link-download-second-stream"
                    >
                      How to Download the Second Stream of the Recording
                    </ExternalLink>
                  </li>
                  <li>
                    <ExternalLink
                      href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq"
                      :icon-size="16"
                      link-id="link-faq"
                    >
                      Course Capture FAQ
                    </ExternalLink>
                  </li>
                </ul>
              </v-col>
            </v-row>
            <ScheduledCourse v-if="currentUser.isAdmin" :course="course" />
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
import {computed, onMounted, reactive, ref} from 'vue'
import {get, isEmpty} from 'lodash'
import {mdiAlert, mdiBookMultipleOutline} from '@mdi/js'
import {storeToRefs} from 'pinia'
import {useRoute} from 'vue-router'
import {getCourseCodes, getTermName} from '@/lib/utils'
import Collaborators from '@/components/course/Collaborators'
import CourseHistory from '@/components/course/CourseHistory'
import CourseNotes from '@/components/course/CourseNotes'
import CoursePageSidebar from '@/components/course/CoursePageSidebar'
import Date from '@/components/util/Date'
import ExternalLink from '@/components/util/ExternalLink'
import {getAuditoriums} from '@/api/room'
import PageTitle from '@/components/util/PageTitle'
import RecordingPlacement from '@/components/course/RecordingPlacement'
import RecordingType from '@/components/course/RecordingType'
import ScheduledCourse from '@/components/course/ScheduledCourse'
import ToggleOptOut from '@/components/course/ToggleOptOut.vue'
import {getCourse} from '@/api/course'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const {config, currentUser, loading} = storeToRefs(contextStore)
const agreedToTerms = ref(false)
const auditoriums = ref([])
const capability = ref()
const course = ref({
  canvasSites: [],
  collaborators: [],
  instructors: [],
  meetings: {
    eligible: [],
    ineligible: []
  },
  note: undefined,
  updateHistory: []
})
const courseDisplayTitle = ref('')
const displayLabels = reactive({
  kaltura_media_gallery: 'Publish to the Media Gallery (all members of the bCourses site will have access)',
  kaltura_my_media: 'Place in My Media (I will decide if and how I want to share)',
  presenter_presentation_audio: 'Camera Without Operator',
  presenter_presentation_audio_with_operator: `Camera With Operator ($${config.value.courseCapturePremiumCost} fee)`
})
const hasValidMeetingTimes = ref(false)
const instructors = ref([])
const instructorProxies = ref([])
const location = ref('')

// Computed
// const disableSubmit = computed(() => !agreedToTerms.value || !publishType.value || !recordingType.value)
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
  return getCourse(termId, sectionId)
    .then(data => {
      course.value = data
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
