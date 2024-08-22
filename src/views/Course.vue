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
          <CoursePageSidebar :course="course" />
          <v-card v-if="$currentUser.isAdmin" outlined class="elevation-1 mt-4">
            <v-card-title>
              Notes
            </v-card-title>
            <v-card-text v-if="!noteEditing" id="note-body">
              {{ course.note || 'No notes.' }}
            </v-card-text>
            <v-card-actions v-if="!noteEditing" class="px-4 pb-4">
              <v-btn
                id="btn-edit-note"
                :disabled="noteUpdating"
                @click="editNote"
              >
                Edit
              </v-btn>
              <v-btn
                v-if="course.note"
                id="btn-delete-note"
                class="mx-3"
                :disabled="noteUpdating"
                @click="deleteNote"
              >
                Delete
              </v-btn>
            </v-card-actions>
            <v-card-text v-if="noteEditing">
              <v-textarea
                id="note-body-edit"
                v-model="noteBody"
                outlined
                hide-details="auto"
                density="compact"
                placeholder="Enter note text"
              >
              </v-textarea>
            </v-card-text>
            <v-card-actions v-if="noteEditing" class="px-4 pb-4">
              <v-btn
                id="btn-save-note"
                color="success"
                :disabled="!noteBody || noteUpdating"
                @click="saveNote"
              >
                Save
              </v-btn>
              <v-btn
                id="btn-cancel-note"
                class="mx-3"
                :disabled="noteUpdating"
                @click="cancelNote"
              >
                Cancel
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
        <v-col>
          <v-container v-if="isCurrentTerm && capability && hasValidMeetingTimes && !course.hasOptedOut && course.scheduled" class="elevation-2 pa-6">
            <v-row>
              <v-col class="font-weight-bold mb-1">
                <v-alert
                  v-if="updatesQueued"
                  density="compact"
                  type="warning"
                  icon="mdi-alert"
                  outlined
                >
                  Recent updates to recording settings are currently queued for publication. They will be published in an hour or less.
                </v-alert>
                <span id="notice-scheduled" class="green--text">
                  {{ $currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture. The first recording is on {{ course.scheduled[0].meetingStartDate | moment('MMM D, YYYY') }}.
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
                <div v-for="instructor in course.instructors" :id="`instructor-${instructor.uid}`" :key="`instructor-${instructor.uid}`">
                  {{ instructor.name }} ({{ instructor.uid }})
                  <span v-if="instructor.hasOptedOut" :id="`instructor-${instructor.uid}-opt-out`">
                    (opted out)
                  </span>
                </div>
              </v-col>
            </v-row>
            <v-row
              v-if="!collaboratorsEditing"
              align="center"
              justify="start"
            >
              <v-col id="collaborators-list" cols="12">
                <h4>
                  Collaborator(s) listed will have editing and publishing access:
                </h4>
                <div v-for="collaborator in collaborators" :id="`collaborator-${collaborator.uid}`" :key="`collaborator-${collaborator.uid}`">
                  {{ collaborator.firstName }} {{ collaborator.lastName }} ({{ collaborator.email }}) ({{ collaborator.uid }})
                </div>
                <div v-if="!collaborators || !collaborators.length" id="collaborators-none">
                  None
                </div>
                <v-btn
                  id="btn-collaborators-edit"
                  class="mt-3"
                  @click="toggleCollaboratorsEditing"
                >
                  Edit
                </v-btn>
              </v-col>
            </v-row>
            <v-card v-if="collaboratorsEditing" class="my-4 background-shaded">
              <v-container>
                <v-row
                  align="center"
                  justify="start"
                >
                  <v-col cols="12">
                    <h4>
                      Update collaborators
                    </h4>
                  </v-col>
                </v-row>
                <v-row
                  align="end"
                  justify="start"
                >
                  <v-col cols="9">
                    <PersonLookup
                      id="input-collaborator-lookup-autocomplete"
                      ref="personLookup"
                      :disabled="collaboratorsUpdating"
                      label="Find collaborator by UID or email address: "
                      placeholder="UID or email"
                      :on-select-result="addCollaboratorPending"
                      :error-message="addCollaboratorError"
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
                    <div
                      v-for="collaborator in collaborators"
                      :id="`collaborator-${collaborator.uid}`"
                      :key="collaborator.uid"
                      class="my-2"
                    >
                      {{ collaborator.firstName }} {{ collaborator.lastName }} ({{ collaborator.email }}) ({{ collaborator.uid }})
                      <v-btn
                        :id="`btn-collaborator-remove-${collaborator.uid}`"
                        :disabled="collaboratorsUpdating"
                        small
                        @click="removeCollaborator(collaborator.uid)"
                      >
                        Remove
                      </v-btn>
                    </div>
                    <div class="mt-4">
                      <v-btn
                        id="btn-collaborators-save"
                        color="success"
                        :disabled="$_.isEqual($_.sortBy(collaborators, 'uid'), $_.sortBy(course.collaborators, 'uid')) || collaboratorsUpdating"
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
                        id="btn-collaborators-cancel"
                        color="default"
                        :disabled="collaboratorsUpdating"
                        class="mx-2"
                        @click="updateCollaboratorsCancel"
                      >
                        Cancel
                      </v-btn>
                    </div>
                  </v-col>
                </v-row>
              </v-container>
            </v-card>
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
                    class="mx-2"
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
                  <div v-if="publishType && publishType.startsWith('kaltura_media_gallery') && course.canvasSiteIds" id="publish-linked-canvas-site">
                    Linked bCourses site(s):
                    <div v-for="site in course.canvasSites" :key="site.canvasSiteId">
                      <CanvasCourseSite :site-id="site.canvasSiteId" :course-site="site" />
                    </div>
                  </div>
                  <v-btn
                    id="btn-publish-type-edit"
                    class="mt-3"
                    @click="togglePublishTypeEditing"
                  >
                    Edit
                  </v-btn>
                </div>
                <v-card v-if="publishTypeEditing" class="my-4 background-shaded">
                  <v-container>
                    <v-radio-group
                      id="select-publish-type"
                      v-model="publishType"
                      class="mt-0"
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
                    <v-row
                      v-if="publishType && publishType.startsWith('kaltura_media_gallery')"
                      align="center"
                      justify="start"
                    >
                      <v-col cols="12">
                        <h4>
                          Linked bCourses site(s):
                        </h4>
                      </v-col>
                    </v-row>
                    <v-row
                      v-if="!$currentUser.isAdmin && publishType && publishType.startsWith('kaltura_media_gallery')"
                      align="end"
                      justify="start"
                    >
                      <v-col cols="9">
                        <v-select
                          id="select-canvas-site"
                          v-model="pendingCanvasSite"
                          :disabled="publishTypeUpdating"
                          :full-width="true"
                          hide-details
                          item-text="name"
                          :item-disabled="item => isCanvasSiteIdStaged(item.canvasSiteId)"
                          return-object
                          :items="publishCanvasSiteOptions"
                          label="Select course site"
                          solo
                        >
                          <span :id="`menu-option-canvas-site-${data.item.canvasSiteId}`" slot="item" slot-scope="data">
                            {{ data.item.name }} ({{ data.item.courseCode }})
                          </span>
                        </v-select>
                      </v-col>
                      <v-col cols="3">
                        <v-btn
                          id="btn-canvas-site-add"
                          color="success"
                          :disabled="!pendingCanvasSite"
                          @click="addCanvasSiteConfirm"
                        >
                          Add
                        </v-btn>
                      </v-col>
                    </v-row>
                    <v-row
                      v-if="$currentUser.isAdmin && publishType && publishType.startsWith('kaltura_media_gallery')"
                      align="end"
                      justify="start"
                    >
                      <v-col cols="9">
                        <v-text-field
                          id="input-canvas-site-id"
                          v-model="pendingCanvasSiteId"
                          label="Enter Canvas site id"
                          :disabled="publishTypeUpdating"
                          hide-details="auto"
                          outlined
                          dense
                        >
                        </v-text-field>
                      </v-col>
                      <v-col cols="3">
                        <v-btn
                          id="btn-canvas-site-add"
                          color="success"
                          :disabled="!pendingCanvasSiteId || !/^\d+$/.test(pendingCanvasSiteId) || isCanvasSiteIdStaged(pendingCanvasSiteId)"
                          @click="addCanvasSiteById"
                        >
                          Add
                        </v-btn>
                      </v-col>
                    </v-row>
                    <v-row
                      v-if="publishType && publishType.startsWith('kaltura_media_gallery')"
                      align="center"
                      justify="start"
                    >
                      <v-col cols="12">
                        <div
                          v-for="site in publishCanvasSites"
                          :id="`canvas-site-${site.canvasSiteId}`"
                          :key="site.canvasSiteId"
                          class="my-2"
                        >
                          {{ site.name }} ({{ site.courseCode }})
                          <v-btn
                            :id="`btn-canvas-site-remove-${site.canvasSiteId}`"
                            :disabled="publishTypeUpdating"
                            small
                            @click="removeCanvasSite(site.canvasSiteId)"
                          >
                            Remove
                          </v-btn>
                        </div>
                      </v-col>
                    </v-row>
                    <v-row
                      align="center"
                      justify="start"
                    >
                      <v-col cols="12">
                        <div>
                          <v-btn
                            id="btn-publish-type-save"
                            color="success"
                            :disabled="publishTypeUpdating || (publishType && publishType.startsWith('kaltura_media_gallery') && !publishCanvasSites.length)"
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
                            class="mx-2"
                            @click="updatePublishTypeCancel"
                          >
                            Cancel
                          </v-btn>
                        </div>
                      </v-col>
                    </v-row>
                  </v-container>
                </v-card>
              </v-col>
            </v-row>
            <v-row v-if="!$currentUser.isAdmin && $_.get(course, 'publishType', '') === 'kaltura_my_media'">
              <v-col cols="12">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li><a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013882">How to Publish from My Media</a></li>
                  <li><a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013623">How to Embed in bCourses using the Rich Content Editor</a></li>
                  <li><a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115">How to Download the Second Stream of the Recording</a></li>
                  <li><a href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq">Course Capture FAQ</a></li>
                </ul>
              </v-col>
            </v-row>
            <v-row v-if="!$currentUser.isAdmin && $_.get(course, 'publishType', '').startsWith('kaltura_media_gallery')">
              <v-col cols="12">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li><a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014032">How to Remove a Recording from the Media Gallery</a></li>
                  <li><a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115">How to Download the Second Stream of the Recording</a></li>
                  <li><a href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq">Course Capture FAQ</a></li>
                </ul>
              </v-col>
            </v-row>
            <v-row v-if="$currentUser.isAdmin">
              <v-col cols="12">
                <ScheduledCourse :course="course"></ScheduledCourse>
              </v-col>
            </v-row>
          </v-container>
          <v-container v-if="isCurrentTerm && capability && hasValidMeetingTimes && !course.deletedAt && (course.hasOptedOut || !course.scheduled)" class="elevation-2 pa-6">
            <v-row>
              <v-col class="font-weight-bold mb-1">
                <span v-if="course.hasOptedOut && !course.scheduled" id="notice-opt-out" class="red--text">
                  {{ $currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture because one or more instructors have opted out. To schedule recordings, please have all instructors remove their opt-out status.
                </span>
                <span v-if="course.hasOptedOut && course.scheduled" id="notice-opt-out-pending" class="red--text">
                  {{ $currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled shortly because one or more instructors have opted out. To keep recordings scheduled, please have all instructors remove their opt-out status.
                </span>
                <span v-if="!course.hasOptedOut" id="notice-eligible-not-scheduled" class="green--text">
                  This course is eligible for scheduling, but has not yet been scheduled. Instructors will be notified when scheduling has taken place.
                </span>
              </v-col>
            </v-row>
            <v-row
              align="center"
              justify="start"
            >
              <v-col id="instructors-list" cols="12">
                <h4>
                  Instructor(s):
                </h4>
                <div v-for="instructor in course.instructors" :id="`instructor-${instructor.uid}`" :key="instructor.uid">
                  {{ instructor.name }} ({{ instructor.uid }})
                  <span v-if="instructor.hasOptedOut" :id="`instructor-${instructor.uid}-opt-out`">
                    (opted out)
                  </span>
                </div>
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
                <span :id="`update-publishedAt-${item.id}`">{{ item.publishedAt ? new Date(item.publishedAt).toLocaleString() : '&mdash;' }}</span>
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
import {
  deleteCourseNote, getCourse, getCourseSite, updateCollaborators,
  updateCourseNote, updatePublishType, updateRecordingType
} from '@/api/course'
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
      addCollaboratorError: null,
      agreedToTerms: false,
      auditoriums: undefined,
      capability: undefined,
      collaborators: undefined,
      collaboratorsEditing: undefined,
      collaboratorsUpdating: undefined,
      course: undefined,
      courseDisplayTitle: null,
      displayLabels: {
        'kaltura_media_gallery': 'Publish to the Media Gallery (all members of the bCourses site will have access)',
        'kaltura_my_media': 'Publish to My Media (I will decide if and how I want to share)',
        'presenter_presentation_audio': 'Camera Without Operator',
        'presenter_presentation_audio_with_operator': `Camera With Operator ($${this.$config.courseCapturePremiumCost} fee)`
      },
      hasValidMeetingTimes: undefined,
      instructors: undefined,
      instructorProxies: undefined,
      instructorProxyPrivileges: undefined,
      location: undefined,
      noteBody: undefined,
      noteEditing: false,
      noteUpdating: false,
      pendingCollaborator: undefined,
      pendingCanvasSite: undefined,
      pendingCanvasSiteId: undefined,
      publishCanvasSites: [],
      publishCanvasSiteOptions: [],
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
    recordingTypeEditable() {
      return this.recordingTypeOptions.length > 1 && (this.$currentUser.isAdmin || this.course.recordingType !== 'presenter_presentation_audio_with_operator')
    },
    updatesQueued() {
      return !!this.$_.find(this.course.updateHistory, {'status': 'queued'})
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
    addCanvasSiteById() {
      if (this.pendingCanvasSiteId && !this.isCanvasSiteIdStaged(this.pendingCanvasSiteId)) {
        getCourseSite(this.pendingCanvasSiteId).then(data => {
          if (data) {
            this.publishCanvasSites.push(data)
            this.alertScreenReader(`Site ${data.name} added.`)
          }
        })
      }
      this.pendingCanvasSiteId = null
    },
    addCanvasSiteConfirm() {
      if (this.pendingCanvasSite && !this.isCanvasSiteIdStaged(this.pendingCanvasSite.canvasSiteId)) {
        this.publishCanvasSites.push(this.pendingCanvasSite)
      }
      this.alertScreenReader(`Site ${this.pendingCanvasSite.name} added.`)
      this.pendingCanvasSite = null
    },
    addCollaboratorConfirm() {
      if (this.$_.find(this.collaborators, {'uid': this.pendingCollaborator.uid})) {
        this.addCollaboratorError = `${this.pendingCollaborator.firstName} ${this.pendingCollaborator.lastName} is already a collaborator.`
        this.alertScreenReader(this.addCollaboratorError)
      } else {
        this.addCollaboratorError = null
        this.collaborators.push(this.pendingCollaborator)
        this.alertScreenReader(`Collaborator ${this.pendingCollaborator.firstName} ${this.pendingCollaborator.lastName} added.`)
      }
      this.alertScreenReader(`Collaborator ${this.pendingCollaborator.firstName} ${this.pendingCollaborator.lastName} added.`)
      this.pendingCollaborator = null
      if (this.$refs.personLookup) {
        this.$refs.personLookup.clear()
      }
    },
    addCollaboratorPending(collaborator) {
      if (collaborator) {
        this.pendingCollaborator = collaborator
        this.addCollaboratorError = null
      }
    },
    cancelNote() {
      this.noteBody = this.course.note
      this.noteEditing = false
      this.noteUpdating = false
      this.alertScreenReader('Note edit canceled.')
    },
    deleteNote() {
      this.noteUpdating = true
      deleteCourseNote(this.course.termId, this.course.sectionId).then(() => {
        this.course.note = this.noteBody = null
        this.noteUpdating = false
        this.alertScreenReader('Note deleted.')
      })
    },
    editNote() {
      this.noteEditing = true
      this.alertScreenReader('Editing note.')
    },
    isCanvasSiteIdStaged(siteId) {
      return !!this.$_.find(this.publishCanvasSites, {'canvasSiteId': parseInt(siteId, 10)})
    },
    removeCanvasSite(canvasSiteId) {
      this.publishCanvasSites = this.$_.filter(this.publishCanvasSites, c => c.canvasSiteId !== canvasSiteId)
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
      this.collaborators = this.$_.clone(this.course.collaborators)
      this.noteBody = this.course.note
      this.publishType = this.course.publishType
      this.recordingType = this.course.recordingType
      this.publishCanvasSites = this.course.canvasSites
      this.recordingTypeOptions = this.meeting.room ? Object.keys(this.meeting.room.recordingTypeOptions) : []
      if (!this.$currentUser.isAdmin) {
        getCanvasSitesTeaching(this.$currentUser.uid).then(data => {
          this.publishCanvasSiteOptions = data
        })
      }
      this.$ready(this.courseDisplayTitle)
    },
    saveNote() {
      this.noteUpdating = true
      updateCourseNote(this.course.termId, this.course.sectionId, this.noteBody).then(data => {
        this.course.note = this.noteBody = data.note
        this.noteEditing = false
        this.noteUpdating = false
        this.alertScreenReader('Note updated.')
      })
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
        this.addCollaboratorError = null
      })
    },
    updateCollaboratorsCancel() {
      this.alertScreenReader('Collaborator update cancelled.')
      this.collaboratorsEditing = false
      this.collaboratorsUpdating = false
      this.addCollaboratorError = null
      this.collaborators = this.$_.clone(this.course.collaborators)
    },
    updatePublishType() {
      this.publishTypeUpdating = true
      updatePublishType(
        this.$_.map(this.publishCanvasSites, 'canvasSiteId'),
        this.publishType,
        this.course.sectionId,
        this.course.termId,
      ).then(data => {
        const message = `Recording placement updated to ${data.publishTypeName}.`
        this.alertScreenReader(message)
        this.course.canvasSiteIds = data.canvasSiteIds
        this.course.canvasSites = data.canvasSites
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
