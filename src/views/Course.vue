<template>
  <div v-if="!loading">
    <v-container fluid>
      <v-row class="pl-3">
        <PageTitle
          v-if="$config.currentTermId === this.course.termId"
          :class-for-h1="course.deletedAt ? 'line-through' : ''"
          icon="mdi-book-multiple-outline"
          :text="courseDisplayTitle"
        />
        <PageTitle
          v-if="$config.currentTermId !== this.course.termId"
          :class-for-h1="course.deletedAt ? 'line-through' : ''"
          icon="mdi-book-multiple-outline"
          :text="`${courseDisplayTitle} (${getTermName(course.termId)})`"
        />
      </v-row>
      <v-row class="ml-8 pl-7">
        <span v-if="course.deletedAt" class="subtitle-1">
          <span class="font-weight-bold red--text">UC Berkeley has canceled this section.</span>
        </span>
        <h2 v-if="!course.deletedAt" id="course-title" class="primary--text">{{ course.courseTitle }}</h2>
      </v-row>
      <v-row class="body-1 ml-8 pl-7">
        Section ID: <span id="section-id">{{ course.sectionId }}</span>
      </v-row>
      <v-row>
        <v-col lg="3" cols="3" sm="3">
          <CoursePageSidebar :after-unschedule="afterUnschedule" :course="course" />
        </v-col>
        <v-col>
          <v-container v-if="isCurrentTerm && capability && hasValidMeetingTimes && !multipleEligibleMeetings" class="elevation-2 pa-6">
            <v-row>
              <v-col id="approvals-described" class="font-weight-medium mb-1 red--text">
                <span v-if="queuedForScheduling && !course.deletedAt">This course is currently queued for scheduling. Recordings will be scheduled in an hour or less. </span>
                <span v-if="approvedByInstructorUIDs.length" class="pr-1">
                  Approved by
                  <OxfordJoin v-slot="{item}" :items="approvedByInstructorUIDs">
                    <CalNetProfile :say-you="true" :uid="item" />
                  </OxfordJoin>.
                </span>
                <span v-if="approvalNeededNames.length && !course.deletedAt">
                  <span v-if="!course.scheduled && !queuedForScheduling">Recordings will be scheduled when we have</span>
                  <span v-if="course.scheduled">Recordings have been scheduled but we need</span>
                  <span v-if="queuedForScheduling">We need</span>
                  {{ approvalNeededNames.length > 1 ? 'approvals' : 'approval' }}
                  from {{ oxfordJoin(approvalNeededNames) }}.
                </span>
                <span v-if="approvedByAdmins.length && !approvalNeededNames.length && !approvedByInstructorUIDs.length">
                  <span v-if="course.scheduled">{{ $currentUser.isAdmin ? 'The' : 'Your' }} course has been scheduled.</span>
                </span>
              </v-col>
            </v-row>
            <v-row v-if="course.scheduled" no-gutters>
              <v-col>
                <ScheduledCourse
                  :after-approve="render"
                  class="px-2"
                  :course="course"
                />
              </v-col>
            </v-row>
            <v-row v-if="hasCurrentUserApproved && !course.scheduled">
              <v-col>
                <v-list>
                  <v-list-item two-line>
                    <v-list-item-content>
                      <v-list-item-title class="pl-3">Recording Type</v-list-item-title>
                      <v-list-item-subtitle id="recording-type-name" class="pl-3">{{ mostRecentApproval.recordingTypeName }}</v-list-item-subtitle>
                    </v-list-item-content>
                    <v-list-item-content>
                      <v-list-item-title>Publish Type</v-list-item-title>
                      <v-list-item-subtitle id="publish-type-name">{{ mostRecentApproval.publishTypeName }}</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
            <v-row v-if="!hasCurrentUserApproved" no-gutters>
              <v-col cols="12">
                <CourseCaptureExplained />
              </v-col>
            </v-row>
            <v-row
              v-if="showSignUpForm"
              align="center"
              justify="start"
              no-gutters
            >
              <v-col cols="10">
                <h4>Allow users with the Admin Proxy role to edit and publish recordings?</h4>
              </v-col>
              <v-col cols="2">
                <v-switch
                  id="can-aprx-instructors-edit-recordings"
                  v-model="canAprxInstructorsEditRecordings"
                  :label="canAprxInstructorsEditRecordings ? 'Yes' : 'No'"
                  @change="v => updateCanAprxInstructorsEditRecordings(v)"
                />
              </v-col>
            </v-row>
            <v-row v-if="meeting.room && !hasCurrentUserApproved" no-gutters>
              <v-col cols="12">
                <div
                  class="font-italic font-weight-light py-2"
                  :class="{'pt-2': meeting.room.isAuditorium}"
                >
                  <v-icon v-if="!meeting.room.isAuditorium">mdi-information-outline</v-icon>
                  Instructors will now be able to review and edit their Course Capture recordings prior to releasing them to students.
                  If you choose 'Instructor moderation', only the instructors listed on this page will be able to release lecture capture videos to your students.
                  If you choose 'GSI/TA moderation', then in addition to instructors, GSI and TA roles will be able to release your lecture capture video to your students.
                  Only instructors listed will be able to edit Course Capture recordings.
                </div>
              </v-col>
            </v-row>
            <v-row
              v-if="showSignUpForm"
              align="center"
              justify="start"
            >
              <v-col cols="3">
                <h4>
                  <label id="select-recording-type-label" for="select-recording-type">Recording Type</label>
                </h4>
              </v-col>
              <v-col cols="9">
                <div v-if="course.hasNecessaryApprovals" id="approved-recording-type">
                  {{ mostRecentApproval.recordingTypeName }}
                </div>
                <div v-if="!course.hasNecessaryApprovals">
                  <div v-if="recordingTypeOptions.length === 1" id="recording-type">
                    {{ recordingTypeOptions[0].text }}
                    <input type="hidden" name="recordingType" :value="recordingTypeOptions[0].value">
                  </div>
                  <div v-if="recordingTypeOptions.length > 1">
                    <v-select
                      id="select-recording-type"
                      v-model="recordingType"
                      :disabled="isApproving"
                      :full-width="true"
                      hide-details
                      item-text="text"
                      item-value="value"
                      :items="recordingTypeOptions"
                      label="Select..."
                      solo
                    >
                      <span :id="`menu-option-recording-type-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item.text }}</span>
                    </v-select>
                  </div>
                </div>
              </v-col>
            </v-row>
            <v-row
              v-if="showSignUpForm"
              align="center"
              justify="start"
            >
              <v-col cols="3">
                <h4>
                  <label id="select-publish-type-label" for="select-publish-type">Publish</label>
                </h4>
              </v-col>
              <v-col cols="9">
                <div v-if="course.hasNecessaryApprovals" id="approved-publish-type">
                  {{ mostRecentApproval.publishTypeName }}
                </div>
                <v-select
                  v-if="!course.hasNecessaryApprovals"
                  id="select-publish-type"
                  v-model="publishType"
                  :disabled="isApproving"
                  :full-width="true"
                  hide-details
                  item-text="text"
                  item-value="value"
                  :items="publishTypeOptions"
                  label="Select..."
                  solo
                >
                  <span :id="`menu-option-publish-type-${data.item.value}`" slot="item" slot-scope="data">{{ data.item.text }}</span>
                </v-select>
              </v-col>
            </v-row>
            <v-row
              v-if="showSignUpForm && instructorProxies.length"
              align="center"
              class="mt-6"
              justify="start"
            >
              <v-col cols="12">
                <span class="font-weight-medium mb-1 red--text">
                  Allow Admin {{ instructorProxies.length === 1 ? 'Proxy' : 'Proxies' }} to edit recordings?
                </span>
              </v-col>
            </v-row>
            <v-row
              v-if="mustAgreeToTerms"
              align="start"
              class="mt-6"
              no-gutters
            >
              <v-col order="12">
                <TermsAgreementText class="pt-1" />
              </v-col>
              <v-col md="auto">
                <v-checkbox
                  id="agree-to-terms-checkbox"
                  v-model="agreedToTerms"
                  class="mt-0"
                  aria-labelledby="permission-agreement"
                ></v-checkbox>
              </v-col>
            </v-row>
            <v-row v-if="showSignUpForm" lg="2">
              <v-col>
                <v-btn
                  id="btn-approve"
                  class="float-right"
                  color="success"
                  :disabled="disableSubmit || isApproving"
                  @click="approve"
                >
                  <v-progress-circular
                    v-if="isApproving"
                    class="mr-2"
                    color="primary"
                    indeterminate
                    size="18"
                    width="3"
                  ></v-progress-circular>
                  {{ isApproving ? 'Approving' : 'Approve' }}
                </v-btn>
              </v-col>
            </v-row>
          </v-container>
          <v-container v-if="isCurrentTerm && !capability">
            <v-row>
              <div class="d-flex justify-start">
                <div class="pr-2">
                  <v-icon color="red">mdi-alert</v-icon>
                </div>
                <div id="course-not-eligible">
                  This course is not eligible for Course Capture because
                  <span v-if="location">{{ location }} is not capture-enabled.</span>
                  <span v-if="!location">it has no meeting location.</span>
                </div>
              </div>
            </v-row>
          </v-container>
          <v-container v-if="multipleEligibleMeetings">
            <v-row>
              <div class="d-flex justify-start">
                <div class="pr-2">
                  <v-icon color="red">mdi-alert</v-icon>
                </div>
                <div id="course-multiple-eligible-meetings">
                  This course does not meet a typical course's meeting pattern and cannot be scheduled automatically.
                  Scheduling requests must be communicated to
                  <a :href="`mailto:${$config.emailCourseCaptureSupport}`" target="_blank">{{ $config.emailCourseCaptureSupport }}</a>.
                </div>
              </div>
            </v-row>
          </v-container>
          <v-container v-if="isCurrentTerm && capability && !multipleEligibleMeetings && !hasValidMeetingTimes">
            <v-row>
              <div class="d-flex justify-start">
                <div class="pr-2">
                  <v-icon color="red">mdi-alert</v-icon>
                </div>
                <div id="invalid-meeting-times">
                  This course is in a capture-enabled room but the meeting times are missing or invalid.
                </div>
              </div>
            </v-row>
          </v-container>
          <v-container v-if="!isCurrentTerm">
            <v-row>
              <div class="d-flex justify-start">
                <div class="pr-2">
                  <v-icon color="red">mdi-alert</v-icon>
                </div>
                <div id="course-not-current">
                  This course is not currently eligible for Course Capture.
                </div>
              </div>
            </v-row>
          </v-container>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import CalNetProfile from '@/components/util/CalNetProfile'
import Context from '@/mixins/Context'
import CourseCaptureExplained from '@/components/util/CourseCaptureExplained'
import CoursePageSidebar from '@/components/course/CoursePageSidebar'
import OxfordJoin from '@/components/util/OxfordJoin'
import PageTitle from '@/components/util/PageTitle'
import ScheduledCourse from '@/components/course/ScheduledCourse'
import TermsAgreementText from '@/components/util/TermsAgreementText'
import Utils from '@/mixins/Utils'
import {approve, getCourse, updateCanAprxInstructorsEditRecordings} from '@/api/course'
import {getAuditoriums} from '@/api/room'

export default {
  name: 'Course',
  mixins: [Context, Utils],
  components: {
    CalNetProfile,
    CourseCaptureExplained,
    CoursePageSidebar,
    OxfordJoin,
    PageTitle,
    ScheduledCourse,
    TermsAgreementText
  },
  data: () => ({
    agreedToTerms: false,
    approvalNeededNames: undefined,
    approvedByAdmins: undefined,
    approvedByInstructorUIDs: undefined,
    auditoriums: undefined,
    canAprxInstructorsEditRecordings: undefined,
    capability: undefined,
    course: undefined,
    courseDisplayTitle: null,
    hasCurrentUserApproved: undefined,
    hasValidMeetingTimes: undefined,
    instructors: undefined,
    instructorProxies: undefined,
    instructorProxyPrivileges: undefined,
    isApproving: false,
    location: undefined,
    multipleEligibleMeetings: undefined,
    publishType: undefined,
    publishTypeOptions: undefined,
    recordingType: undefined,
    recordingTypeOptions: undefined
  }),
  computed: {
    disableSubmit() {
      return !this.agreedToTerms || !this.publishType || !this.recordingType
    },
    isCurrentTerm() {
      return this.course.termId === this.$config.currentTermId
    },
    mustAgreeToTerms() {
      return this.showSignUpForm && !this.$currentUser.isAdmin
    },
    mostRecentApproval() {
      return this.$_.last(this.course.approvals)
    },
    queuedForScheduling() {
      return this.course.hasNecessaryApprovals && !this.course.scheduled
    },
    showSignUpForm() {
      let show = !this.course.scheduled && !this.hasCurrentUserApproved && !this.course.deletedAt
      show &&= (this.$currentUser.isAdmin || this.$_.map(this.instructors, 'uid').includes(this.$currentUser.uid))
      return show
    }
  },
  created() {
    this.$loading()
    const termId = this.$_.get(this.$route, 'params.termId')
    const sectionId = this.$_.get(this.$route, 'params.sectionId')
    getCourse(termId, sectionId).then(data => {
      this.render(data)
      this.publishTypeOptions = []
      this.$_.each(this.$config.publishTypeOptions, (text, value) => {
        this.publishTypeOptions.push({text, value})
      })
      getAuditoriums().then(data => {
        this.auditoriums = data
      })
    })
  },
  methods: {
    afterUnschedule(data) {
      this.publishType = undefined
      this.recordingType = undefined
      this.render(data)
    },
    approve() {
      this.isApproving = true
      approve(
        this.publishType,
        this.recordingType,
        this.course.sectionId,
        this.instructorProxies
      ).then(data => {
        this.render(data)
        this.isApproving = false
        this.alertScreenReader(`You have approved ${this.courseDisplayTitle} for Course Capture.`)
      })
    },
    render(data) {
      this.$loading()
      this.agreedToTerms = this.$currentUser.isAdmin
      this.course = data
      this.canAprxInstructorsEditRecordings = this.course.canAprxInstructorsEditRecordings
      this.instructors = this.$_.filter(this.course.instructors, i => i.roleCode !== 'APRX')
      this.instructorProxies = this.$_.filter(this.course.instructors, i => i.roleCode === 'APRX')
      // Meetings
      const eligibleMeetings = this.course.meetings.eligible
      this.meeting = eligibleMeetings[0] || this.course.meetings.ineligible[0]
      if (this.meeting.room) {
        this.capability = this.meeting.room.capability
        this.location = this.meeting.room.location
      }
      this.multipleEligibleMeetings = (eligibleMeetings.length > 1)
      this.$_.each(['endDate', 'endTime', 'startDate', 'startTime'], key => {
        this.hasValidMeetingTimes = !!this.$_.find(eligibleMeetings, key)
        return this.hasValidMeetingTimes
      })
      // Approvals
      const approvals = this.course.approvals
      this.approvedByInstructorUIDs = this.$_.map(this.$_.filter(approvals, a => !a.wasApprovedByAdmin), 'approvedBy')
      this.approvedByAdmins = this.$_.filter(approvals, a => a.wasApprovedByAdmin)
      this.approvalNeededNames = []
      this.$_.each(this.instructors, instructor => {
        if (!this.$_.includes(this.approvedByInstructorUIDs, instructor.uid)) {
          this.approvalNeededNames.push(instructor.uid === this.$currentUser.uid ? 'you' : instructor.name)
        }
      })
      this.courseDisplayTitle = this.getCourseCodes(this.course)[0]
      this.hasCurrentUserApproved = this.$_.includes(this.$_.map(approvals, 'approvedBy'), this.$currentUser.uid)
      const recordingTypeOptions = this.meeting.room ? this.meeting.room.recordingTypeOptions : []
      this.recordingTypeOptions = this.$_.map(recordingTypeOptions, (text, value) => {
        const premiumCost = this.$config.courseCapturePremiumCost
        return {
          text: text.includes('with_operator') && premiumCost ? `${text} ($${premiumCost})` : text,
          value
        }
      })
      if (approvals.length) {
        const mostRecent = this.$_.last(approvals)
        this.publishType = mostRecent.publishType
        this.recordingType = mostRecent.recordingType
      } else {
        if (this.recordingTypeOptions.length === 1) {
          this.recordingType = this.recordingTypeOptions[0].value
        }
      }
      this.$ready(this.courseDisplayTitle)
    },
    updateCanAprxInstructorsEditRecordings(value) {
      updateCanAprxInstructorsEditRecordings(
        value,
        this.course.sectionId,
        this.course.termId,
      ).then(() => {
        this.alertScreenReader(`You have approved ${this.courseDisplayTitle} for Course Capture.`)
      })
    }
  }
}
</script>
