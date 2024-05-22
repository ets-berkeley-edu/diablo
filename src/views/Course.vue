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
              <v-col class="font-weight-bold mb-1 green--text">
                <span v-if="!course.scheduled && !course.deletedAt">This course is not currently scheduled.</span>
                <span v-if="course.scheduled">
                  <span v-if="course.scheduled">{{ $currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture.</span>
                </span>
              </v-col>
            </v-row>
            <v-row
              align="center"
              justify="start"
            >
              <v-col id="instructors-list" cols="12">
                <h4>
                  Instructor(s) listed will have editing and publishing access:
                </h4>
                <div v-for="instructor in course.instructors" :id="`instructor-${instructor.uid}`" :key="instructor.uid">
                  {{ instructor.name }} ({{ instructor.uid }})
                </div>
              </v-col>
            </v-row>
            <v-row
              align="center"
              justify="start"
            >
              <v-col id="collaborators-list" cols="12">
                <h4>
                  Collaborator(s) listed will have editing and publishing access:
                </h4>
                <div v-for="collaborator in collaborators" :id="`collaborator-${collaborator.uid}`" :key="collaborator.uid">
                  {{ collaborator.firstName }} {{ collaborator.lastName }} ({{ collaborator.email }}) ({{ collaborator.uid }})
                  <v-btn
                    v-if="collaboratorsEditing"
                    :id="`btn-collaborator-remove-${collaborator.uid}`"
                    text
                    :disabled="collaboratorsUpdating"
                    @click="removeCollaborator(collaborator.uid)"
                  >
                    (remove)
                  </v-btn>
                </div>
                <div v-if="!collaborators.length" id="collaborators-none">
                  None
                </div>
                <div v-if="!collaboratorsEditing">
                  <v-btn
                    id="btn-collaborators-edit"
                    text
                    @click="toggleCollaboratorsEditing"
                  >
                    (edit)
                  </v-btn>
                </div>
              </v-col>
            </v-row>
            <v-row
              v-if="collaboratorsEditing"
              align="end"
              justify="end"
            >
              <v-col cols="9">
                <PersonLookup
                  id="input-collaborator-lookup-autocomplete"
                  ref="personLookup"
                  :disabled="collaboratorsUpdating"
                  label="Find collaborator by UID or email address: "
                  :on-select-result="addCollaboratorPending"
                />
              </v-col>
              <v-col cols="3">
                <v-btn
                  id="btn-collaborator-add"
                  color="success"
                  :disabled="!pendingCollaborator"
                  @click="addCollaboratorConfirm"
                >
                  Add
                </v-btn>
              </v-col>
            </v-row>
            <v-row
              v-if="collaboratorsEditing"
              align="center"
              justify="start"
            >
              <v-col cols="12">
                <v-btn
                  id="btn-collaborators-save"
                  color="success"
                  :disabled="collaboratorsUpdating"
                  @click="updateCollaborators"
                >
                  <v-progress-circular
                    v-if="collaboratorsUpdating"
                    class="mr-2"
                    color="primary"
                    indeterminate
                    size="18"
                    width="3"
                  ></v-progress-circular>
                  {{ collaboratorsUpdating ? 'Saving' : 'Save' }}
                </v-btn>
                <v-btn
                  id="btn-recording-type-cancel"
                  color="default"
                  :disabled="collaboratorsUpdating"
                  @click="updateCollaboratorsCancel"
                >
                  Cancel
                </v-btn>
              </v-col>
            </v-row>
            <v-row
              align="center"
              justify="start"
            >
              <v-col cols="4">
                <h4>
                  <label id="select-recording-type-label" for="select-recording-type">Recording Type</label>
                  <v-btn
                    v-if="recordingTypeEditable"
                    id="btn-recording-type-edit"
                    text
                    :disabled="recordingTypeEditing"
                    @click="toggleRecordingTypeEditing"
                  >
                    (edit)
                  </v-btn>
                </h4>
              </v-col>
              <v-col v-if="!recordingTypeEditing" cols="8">
                <div id="recording-type">
                  {{ course.recordingTypeName }}
                </div>
              </v-col>
              <v-col v-if="recordingTypeEditing && recordingTypeEditable" cols="5">
                <v-select
                  id="select-recording-type"
                  v-model="recordingType"
                  :disabled="recordingTypeUpdating"
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
              </v-col>
              <v-col v-if="recordingTypeEditing && recordingTypeEditable" cols="3">
                <v-btn
                  id="btn-recording-type-save"
                  class="float-right"
                  color="success"
                  :disabled="recordingTypeUpdating"
                  @click="updateRecordingType"
                >
                  <v-progress-circular
                    v-if="recordingTypeUpdating"
                    class="mr-2"
                    color="primary"
                    indeterminate
                    size="18"
                    width="3"
                  ></v-progress-circular>
                  {{ recordingTypeUpdating ? 'Saving' : 'Save' }}
                </v-btn>
                <v-btn
                  id="btn-recording-type-cancel"
                  class="float-right"
                  color="default"
                  :disabled="recordingTypeUpdating"
                  @click="updateRecordingTypeCancel"
                >
                  Cancel
                </v-btn>
              </v-col>
            </v-row>
            <v-row
              align="center"
              justify="start"
            >
              <v-col cols="4">
                <h4>
                  <label id="select-publish-type-label" for="select-publish-type">Recording Placement</label>
                  <v-btn
                    id="btn-publish-type-edit"
                    text
                    :disabled="publishTypeEditing"
                    @click="togglePublishTypeEditing"
                  >
                    (edit)
                  </v-btn>
                </h4>
              </v-col>
              <v-col v-if="!publishTypeEditing" cols="8">
                <div id="publish-type">
                  {{ course.publishTypeName }}
                </div>
              </v-col>
              <v-col v-if="publishTypeEditing" cols="5">
                <v-select
                  v-if="publishTypeEditing"
                  id="select-publish-type"
                  v-model="publishType"
                  :disabled="publishTypeUpdating"
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
              <v-col v-if="publishTypeEditing" cols="3">
                <v-btn
                  id="btn-publish-type-save"
                  class="float-right"
                  color="success"
                  :disabled="publishTypeUpdating"
                  @click="updatePublishType"
                >
                  <v-progress-circular
                    v-if="publishTypeUpdating"
                    class="mr-2"
                    color="primary"
                    indeterminate
                    size="18"
                    width="3"
                  ></v-progress-circular>
                  {{ publishTypeUpdating ? 'Saving' : 'Save' }}
                </v-btn>
                <v-btn
                  id="btn-publish-type-cancel"
                  class="float-right"
                  color="default"
                  :disabled="publishTypeUpdating"
                  @click="updatePublishTypeCancel"
                >
                  Cancel
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
          <v-container v-if="isCurrentTerm && capability && !hasValidMeetingTimes">
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
import Context from '@/mixins/Context'
import CoursePageSidebar from '@/components/course/CoursePageSidebar'
import PageTitle from '@/components/util/PageTitle'
import PersonLookup from '@/components/util/PersonLookup'
import Utils from '@/mixins/Utils'
import {getCourse, updateCollaborators, updatePublishType, updateRecordingType} from '@/api/course'
import {getAuditoriums} from '@/api/room'

export default {
  name: 'Course',
  mixins: [Context, Utils],
  components: {
    CoursePageSidebar,
    PageTitle,
    PersonLookup,
  },
  data: () => ({
    agreedToTerms: false,
    auditoriums: undefined,
    capability: undefined,
    collaborators: undefined,
    collaboratorsEditing: undefined,
    collaboratorsUpdating: undefined,
    course: undefined,
    courseDisplayTitle: null,
    hasValidMeetingTimes: undefined,
    instructors: undefined,
    instructorProxies: undefined,
    instructorProxyPrivileges: undefined,
    location: undefined,
    multipleEligibleMeetings: undefined,
    pendingCollaborator: undefined,
    publishType: undefined,
    publishTypeEditing: false,
    publishTypeOptions: undefined,
    publishTypeUpdating: false,
    recordingType: undefined,
    recordingTypeEditing: false,
    recordingTypeOptions: undefined,
    recordingTypeUpdating: false
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
    recordingTypeEditable() {
      return this.recordingTypeOptions.length > 1 && this.course.recordingType !== 'presenter_presentation_audio_with_operator'
    },
    showSignUpForm() {
      let show = !this.course.scheduled && !this.course.deletedAt
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
    addCollaboratorConfirm() {
      this.collaborators.push(this.pendingCollaborator)
      this.alertScreenReader(`Collaborator ${this.pendingCollaborator.firstName} ${this.pendingCollaborator.lastName} added.`)
      this.pendingCollaborator = null
      if (this.$refs.personLookup) {
        this.$refs.personLookup.clear()
      }
    },
    addCollaboratorPending(collaborator) {
      if (collaborator) {
        this.pendingCollaborator = collaborator
      }
    },
    afterUnschedule(data) {
      this.publishType = undefined
      this.recordingType = undefined
      this.render(data)
    },
    removeCollaborator(uid) {
      this.collaborators = this.$_.filter(this.collaborators, c => c.uid !== uid)
    },
    render(data) {
      this.$loading()
      this.agreedToTerms = this.$currentUser.isAdmin
      this.course = data
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

      this.courseDisplayTitle = this.getCourseCodes(this.course)[0]
      const recordingTypeOptions = this.meeting.room ? this.meeting.room.recordingTypeOptions : []
      this.recordingTypeOptions = this.$_.map(recordingTypeOptions, (text, value) => {
        const premiumCost = this.$config.courseCapturePremiumCost
        return {
          text: text.includes('with_operator') && premiumCost ? `${text} ($${premiumCost})` : text,
          value
        }
      })
      this.collaborators = this.course.collaborators
      this.publishType = this.course.publishType
      this.recordingType = this.course.recordingType
      this.$ready(this.courseDisplayTitle)
    },
    toggleCollaboratorsEditing() {
      this.collaboratorsEditing = true
      this.alertScreenReader('Editing collaborators.')
    },
    togglePublishTypeEditing() {
      this.publishTypeEditing = true
      this.alertScreenReader('Select recording placement.')
    },
    toggleRecordingTypeEditing() {
      this.recordingTypeEditing = true
      this.alertScreenReader('Select recording type.')
    },
    updateCollaborators() {
      this.collaboratorsUpdating = true
      updateCollaborators(
        this.$_.map(this.collaborators, 'uid'),
        this.course.sectionId,
        this.course.termId,
      ).then(data => {
        this.alertScreenReader('Collaborators updated.')
        this.course.collaborators = data.collaborators
        this.collaboratorsEditing = false
        this.collaboratorsUpdating = false
      })
    },
    updateCollaboratorsCancel() {
      this.alertScreenReader('Collaborator update cancelled.')
      this.publishTypeEditing = false
      this.collaborators = this.course.collaborators
    },
    updatePublishType() {
      this.publishTypeUpdating = true
      updatePublishType(
        this.publishType,
        this.course.sectionId,
        this.course.termId,
      ).then(data => {
        const message = `Recording placement updated to ${data.publishTypeName}.`
        this.alertScreenReader(message)
        this.course.publishType = data.publishType
        this.course.publishTypeName = data.publishTypeName
        this.publishTypeEditing = false
        this.publishTypeUpdating = false
      })
    },
    updatePublishTypeCancel() {
      this.alertScreenReader('Publish type update cancelled.')
      this.publishTypeEditing = false
    },
    updateRecordingType() {
      this.recordingTypeUpdating = true
      updateRecordingType(
        this.recordingType,
        this.course.sectionId,
        this.course.termId,
      ).then(data => {
        const message = `Recording type updated to ${this.recordingType.value}.`
        this.alertScreenReader(message)
        this.course.recordingType = data.recordingType
        this.course.recordingTypeName = data.recordingTypeName
        this.recordingTypeEditing = false
        this.recordingTypeUpdating = false
      })
    },
    updateRecordingTypeCancel() {
      this.alertScreenReader('Recording type update cancelled.')
      this.publishTypeEditing = false
    },
  }
}
</script>
