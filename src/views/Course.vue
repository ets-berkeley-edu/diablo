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
          <CoursePageSidebar :course="course" :course-site="courseSite" />
        </v-col>
        <v-col>
          <v-container v-if="isCurrentTerm && capability && hasValidMeetingTimes" class="elevation-2 pa-6">
            <v-row>
              <v-col class="font-weight-bold mb-1">
                <span v-if="course.scheduled && !course.hasOptedOut" id="notice-scheduled" class="green--text">
                  {{ $currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture. The first recording is on {{ course.scheduled[0].meetingStartDate | moment('MMM D, YYYY') }}.
                </span>
                <span v-if="!course.scheduled && !course.deletedAt" id="notice-scheduled" class="red--text">
                  This course is not currently scheduled.
                </span>
                <span v-if="course.hasOptedOut" id="notice-opt-out" class="red--text">
                  {{ $currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture because one or more instructors have opted out. To schedule recordings, please have all instructors remove their opt-out status.
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
                  <span v-if="instructor.hasOptedOut" :id="`instructor-${instructor.uid}-opt-out`">
                    (opted out)
                  </span>
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
                    :disabled="collaboratorsUpdating"
                    @click="removeCollaborator(collaborator.uid)"
                  >
                    Remove
                  </v-btn>
                </div>
                <div v-if="!collaborators.length" id="collaborators-none">
                  None
                </div>
                <div v-if="!collaboratorsEditing">
                  <v-btn
                    id="btn-collaborators-edit"
                    class="mt-3"
                    @click="toggleCollaboratorsEditing"
                  >
                    Edit
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
                  placeholder="UID or email"
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
              <v-col cols="12">
                <h4>
                  <label id="select-recording-type-label" for="select-recording-type">Recording Type</label>
                </h4>
                <div v-if="!recordingTypeEditing">
                  <div id="recording-type-name">
                    {{ displayLabels[course.recordingType] }}
                  </div>
                  <v-btn
                    v-if="recordingTypeEditable"
                    id="btn-recording-type-edit"
                    class="mt-3"
                    @click="toggleRecordingTypeEditing"
                  >
                    Edit
                  </v-btn>
                </div>
                <v-radio-group
                  v-if="recordingTypeEditing && recordingTypeEditable"
                  id="select-recording-type"
                  v-model="recordingType"
                  :disabled="recordingTypeUpdating"
                >
                  <v-radio
                    v-for="recordingTypeOption in recordingTypeOptions"
                    :id="`radio-recording-type-${recordingTypeOption}`"
                    :key="recordingTypeOption"
                    :value="recordingTypeOption"
                    :label="displayLabels[recordingTypeOption]"
                  ></v-radio>
                </v-radio-group>
                <div v-if="recordingTypeEditing && recordingTypeEditable">
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
                </div>
              </v-col>
            </v-row>
            <v-row
              align="center"
              justify="start"
            >
              <v-col cols="12">
                <h4>
                  <label id="select-publish-type-label" for="select-publish-type">Recording Placement</label>
                </h4>
                <div v-if="!publishTypeEditing">
                  <div id="publish-type-name">
                    {{ displayLabels[course.publishType] }}
                  </div>
                  <div v-if="publishType && publishType.startsWith('kaltura_media_gallery') && course.canvasSiteId" id="publish-linked-canvas-site">
                    Linked bCourses site: <CanvasCourseSite :site-id="publishCanvasSiteId" :course-site="courseSite" />
                  </div>
                  <v-btn
                    id="btn-publish-type-edit"
                    class="mt-3"
                    @click="togglePublishTypeEditing"
                  >
                    Edit
                  </v-btn>
                </div>
                <v-radio-group
                  v-if="publishTypeEditing"
                  id="select-publish-type"
                  v-model="publishType"
                  :disabled="publishTypeUpdating"
                >
                  <v-radio
                    v-for="publishTypeOption in publishTypeOptions"
                    :id="`radio-publish-type-${publishTypeOption}`"
                    :key="publishTypeOption"
                    :value="publishTypeOption"
                    :label="displayLabels[publishTypeOption]"
                  ></v-radio>
                </v-radio-group>
                <div v-if="publishTypeEditing && publishType && publishType.startsWith('kaltura_media_gallery')" class="mb-4">
                  <v-select
                    v-if="publishTypeEditing"
                    id="select-canvas-site"
                    v-model="publishCanvasSiteId"
                    :disabled="publishTypeUpdating"
                    :full-width="true"
                    hide-details
                    item-text="name"
                    item-value="canvasSiteId"
                    :items="publishCanvasSiteOptions"
                    label="Select course site"
                    solo
                  >
                    <span :id="`menu-option-canvas-site-${data.item.canvasSiteId}`" slot="item" slot-scope="data">
                      {{ data.item.name }} ({{ data.item.courseCode }})
                    </span>
                  </v-select>
                </div>
                <div v-if="publishTypeEditing">
                  <v-btn
                    id="btn-publish-type-save"
                    color="success"
                    :disabled="publishTypeUpdating || (publishType && publishType.startsWith('kaltura_media_gallery') && !publishCanvasSiteId)"
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
                    color="default"
                    :disabled="publishTypeUpdating"
                    @click="updatePublishTypeCancel"
                  >
                    Cancel
                  </v-btn>
                </div>
              </v-col>
            </v-row>
            <v-row v-if="!$currentUser.isAdmin">
              <v-col cols="12">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li><a href="https://www.berkeley.edu">How to Publish with Selected Students</a></li>
                  <li><a href="https://www.berkeley.edu">How to Embed</a></li>
                  <li><a href="https://www.berkeley.edu">How to Publish with All Students</a></li>
                  <li><a href="https://www.berkeley.edu">How to Unpublish</a></li>
                </ul>
              </v-col>
            </v-row>
            <v-row v-if="$currentUser.isAdmin">
              <v-col cols="12">
                <ScheduledCourse :course="course"></ScheduledCourse>
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
      <v-row v-if="$currentUser.isAdmin">
        <v-col cols="12">
          <v-container id="update-history" class="elevation-2 pa-6 mx-0">
            <h2>Update history</h2>
            <div v-if="!course.updateHistory.length" id="no-updates">No updates.</div>
            <v-data-table
              v-if="course.updateHistory.length"
              id="update-history-table"
              disable-pagination
              :headers="updateHistoryHeaders"
              :hide-default-footer="true"
              :items="course.updateHistory"
              :items-per-page="100"
              class="elevation-1"
            >
              <template #item.fieldName="{ item }">
                <span :id="`update-fieldName-${item.id}`">{{ item.fieldName || '&mdash;' }}</span>
              </template>
              <template #item.fieldValueOld="{ item }">
                <span :id="`update-fieldValueOld-${item.id}`">{{ item.fieldValueOld || '&mdash;' }}</span>
              </template>
              <template #item.fieldValueNew="{ item }">
                <span :id="`update-fieldValueNew-${item.id}`">{{ item.fieldValueNew || '&mdash;' }}</span>
              </template>
              <template #item.requestedByName="{ item }">
                <span :id="`update-requestedByName-${item.id}`">{{ item.requestedByName ? `${item.requestedByName} (${item.requestedByUid})` : '&mdash;' }}</span>
              </template>
              <template #item.requestedAt="{ item }">
                <span :id="`update-requestedAt-${item.id}`">{{ new Date(item.requestedAt).toLocaleString() }}</span>
              </template>
              <template #item.publishedAt="{ item }">
                <span :id="`update-publishedAt-${item.id}`">{{ new Date(item.publishedAt).toLocaleString() }}</span>
              </template>
              <template #item.status="{ item }">
                <span :id="`update-status-${item.id}`">{{ item.status || '&mdash;' }}</span>
              </template>
            </v-data-table>
          </v-container>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import CanvasCourseSite from '@/components/course/CanvasCourseSite'
import Context from '@/mixins/Context'
import CoursePageSidebar from '@/components/course/CoursePageSidebar'
import PageTitle from '@/components/util/PageTitle'
import PersonLookup from '@/components/util/PersonLookup'
import ScheduledCourse from '@/components/course/ScheduledCourse'
import Utils from '@/mixins/Utils'
import {getCourse, updateCollaborators, updatePublishType, updateRecordingType} from '@/api/course'
import {getAuditoriums} from '@/api/room'
import {getCanvasSitesTeaching} from '@/api/user'

export default {
  name: 'Course',
  mixins: [Context, Utils],
  components: {
    CanvasCourseSite,
    CoursePageSidebar,
    PageTitle,
    PersonLookup,
    ScheduledCourse,
  },
  data() {
    return {
      agreedToTerms: false,
      auditoriums: undefined,
      capability: undefined,
      collaborators: undefined,
      collaboratorsEditing: undefined,
      collaboratorsUpdating: undefined,
      course: undefined,
      courseDisplayTitle: null,
      courseSite: undefined,
      displayLabels: {
        'kaltura_media_gallery': 'Publish automatically to the Media Gallery (all members of the bCourses site will have access)',
        'kaltura_media_gallery_moderated': 'Publish to Pending tab (Teacher/TA/Designer members of the bCourses site can approve recordings for viewing)',
        'kaltura_my_media': 'Publish to My Media (I will decide if and how I want to share)',
        'presenter_presentation_audio': 'Camera Without Operator',
        'presenter_presentation_audio_with_operator': `Camera With Operator ($${this.$config.courseCapturePremiumCost} fee)`
      },
      hasValidMeetingTimes: undefined,
      instructors: undefined,
      instructorProxies: undefined,
      instructorProxyPrivileges: undefined,
      location: undefined,
      pendingCollaborator: undefined,
      publishCanvasSiteId: undefined,
      publishCanvasSiteOptions: undefined,
      publishType: undefined,
      publishTypeEditing: false,
      publishTypeOptions: undefined,
      publishTypeUpdating: false,
      recordingType: undefined,
      recordingTypeEditing: false,
      recordingTypeOptions: undefined,
      recordingTypeUpdating: false,
      updateHistoryHeaders: [
        {text: 'Field', value: 'fieldName'},
        {text: 'Old Value', value: 'fieldValueOld'},
        {text: 'New Value', value: 'fieldValueNew'},
        {text: 'Requested by', value: 'requestedByName', width: '130px'},
        {text: 'Requested at', value: 'requestedAt', width: '130px'},
        {text: 'Published at', value: 'publishedAt', width: '130px'},
        {text: 'Status', value: 'status'}
      ]
    }
  },
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
      // 'kaltura_my_media' comes before 'kaltura_media_gallery'.
      this.publishTypeOptions = Object.keys(this.$config.publishTypeOptions).sort().reverse()
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
      this.$_.each(['endDate', 'endTime', 'startDate', 'startTime'], key => {
        this.hasValidMeetingTimes = !!this.$_.find(eligibleMeetings, key)
        return this.hasValidMeetingTimes
      })
      this.courseDisplayTitle = this.getCourseCodes(this.course)[0]
      this.collaborators = this.course.collaborators
      this.publishType = this.course.publishType
      this.recordingType = this.course.recordingType
      this.recordingTypeOptions = this.meeting.room ? Object.keys(this.meeting.room.recordingTypeOptions) : []
      getCanvasSitesTeaching(this.$currentUser.uid).then(data => {
        this.publishCanvasSiteId = this.course.canvasSiteId
        this.publishCanvasSiteOptions = data
        this.courseSite = this.$_.find(this.publishCanvasSiteOptions, {canvasSiteId: this.publishCanvasSiteId})
      })
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
      this.collaboratorsEditing = false
      this.collaboratorsUpdating = false
      this.collaborators = this.course.collaborators
    },
    updatePublishType() {
      this.publishTypeUpdating = true
      updatePublishType(
        this.publishCanvasSiteId,
        this.publishType,
        this.course.sectionId,
        this.course.termId,
      ).then(data => {
        const message = `Recording placement updated to ${data.publishTypeName}.`
        this.alertScreenReader(message)
        this.course.canvasSiteId = parseInt(data.canvasSiteId, 10)
        this.courseSite = this.$_.find(this.publishCanvasSiteOptions, {canvasSiteId: this.course.canvasSiteId})
        this.course.publishType = data.publishType
        this.course.publishTypeName = data.publishTypeName
        this.publishTypeEditing = false
        this.publishTypeUpdating = false
      })
    },
    updatePublishTypeCancel() {
      this.alertScreenReader('Recording placement update cancelled.')
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
      this.recordingTypeEditing = false
    },
  }
}
</script>
