<template>
  <div v-if="!isLoading">
    <v-container fluid class="px-sm-0">
      <v-row class="pl-3">
        <PageTitle
          v-if="config.currentTermId === course.termId"
          :class-for-h1="course.deletedAt ? 'line-through' : ''"
          :icon="mdiBookMultipleOutline"
          :text="courseDisplayTitle"
        />
        <PageTitle
          v-if="config.currentTermId !== course.termId"
          :class-for-h1="course.deletedAt ? 'line-through' : ''"
          :icon="mdiBookMultipleOutline"
          :text="`${courseDisplayTitle} (${getTermName(course.termId)})`"
        />
      </v-row>
      <v-row class="ml-8 pl-7">
        <span v-if="course.deletedAt" class="subtitle-1">
          <span class="font-weight-bold text-red">UC Berkeley has canceled this section.</span>
        </span>
        <h2 v-if="!course.deletedAt" id="course-title" class="text-primary">{{ course.courseTitle }}</h2>
      </v-row>
      <v-row class="body-1 ml-8 pl-7">
        Section ID: <span id="section-id">{{ course.sectionId }}</span>
      </v-row>
      <v-row>
        <v-col cols="12" md="3" sm="4">
          <CoursePageSidebar :course="course" />
          <v-card v-if="currentUser.isAdmin" outlined class="elevation-1 mt-4">
            <v-card-title>
              Notes
            </v-card-title>
            <v-card-text v-if="!noteEditing" id="note-body">
              {{ course.note || 'No notes.' }}
            </v-card-text>
            <v-card-actions v-if="!noteEditing" class="px-4 pb-4">
              <v-btn
                id="btn-edit-note"
                aria-label="Edit note"
                :disabled="noteUpdating"
                variant="elevated"
                @click="editNote"
              >
                Edit
              </v-btn>
              <v-btn
                v-if="course.note"
                id="btn-delete-note"
                aria-label="Delete Note"
                class="mx-3"
                :disabled="noteUpdating"
                variant="elevated"
                @click="deleteNote"
              >
                Delete
              </v-btn>
            </v-card-actions>
            <v-card-text v-if="noteEditing">
              <v-textarea
                id="note-body-edit"
                v-model="noteBody"
                density="compact"
                hide-details="auto"
                placeholder="Enter note text"
                variant="outlined"
              >
              </v-textarea>
            </v-card-text>
            <v-card-actions v-if="noteEditing" class="px-4 pb-4">
              <ProgressButton
                id="btn-save-note"
                :action="saveNote"
                aria-label="Save Note"
                :disabled="!noteBody || noteUpdating"
                :in-progress="noteUpdating"
                :text="noteUpdating ? 'Saving' : 'Save'"
              />
              <v-btn
                id="btn-cancel-note"
                aria-label="Cancel Note Edit"
                class="mx-3"
                :disabled="noteUpdating"
                variant="elevated"
                @click="cancelNote"
              >
                Cancel
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
        <v-col cols="12" md="9" sm="8">
          <v-container v-if="isCurrentTerm && capability && hasValidMeetingTimes && !course.hasOptedOut && course.scheduled" class="elevation-2 pa-6 px-sm-2">
            <v-row>
              <v-col class="font-weight-bold mb-1">
                <v-alert
                  v-if="updatesQueued"
                  density="compact"
                  type="warning"
                  :icon="mdiAlert"
                  outlined
                >
                  Recent updates to recording settings are currently queued for publication. They will be published in an hour or less.
                </v-alert>
                <span id="notice-scheduled" class="text-green">
                  {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture. The first recording is on
                  {{ DateTime.fromISO(course.scheduled[0].meetingStartDate).toFormat('MMM d, yyyy') }}.
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
                  {{ collaboratorLabel(collaborator) }}
                </div>
                <div v-if="!collaborators || !collaborators.length" id="collaborators-none">
                  None
                </div>
                <v-btn
                  id="btn-collaborators-edit"
                  aria-label="Edit Collaborators"
                  class="mt-3"
                  @click="toggleCollaboratorsEditing"
                >
                  Edit
                </v-btn>
              </v-col>
            </v-row>
            <v-card v-if="collaboratorsEditing" class="bg-surface-light my-4">
              <v-container>
                <v-row
                  align="center"
                  aria-live="polite"
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
                      ref="personLookup"
                      :disabled="collaboratorsUpdating"
                      :error-message="addCollaboratorError"
                      id-prefix="collaborator-lookup"
                      label="Find collaborator"
                      list-label="collaborators"
                      :on-select-result="addCollaboratorConfirm"
                    />
                  </v-col>
                </v-row>
                <v-row
                  v-if="collaboratorsEditing"
                  align="center"
                  justify="start"
                >
                  <v-col cols="12">
                    <div
                      v-for="(collaborator, index) in collaborators"
                      :id="`collaborator-${collaborator.uid}`"
                      :key="collaborator.uid"
                      class="my-2"
                    >
                      {{ collaboratorLabel(collaborator) }}
                      <v-btn
                        :id="`btn-collaborator-remove-${collaborator.uid}`"
                        :aria-label="`Remove ${collaborator.firstName || ''} ${collaborator.lastName || ''} as collaborator`"
                        :disabled="collaboratorsUpdating"
                        small
                        @click="removeCollaborator(collaborator.uid, index)"
                      >
                        Remove
                      </v-btn>
                    </div>
                    <div class="mt-4">
                      <ProgressButton
                        id="btn-collaborators-save"
                        :action="updateCollaboratorsClicked"
                        aria-label="Save Collaborators"
                        :disabled="isEqual(sortBy(collaborators, 'uid'), sortBy(course.collaborators, 'uid')) || collaboratorsUpdating"
                        :in-progress="collaboratorsUpdating"
                        :text="collaboratorsUpdating ? 'Saving' : 'Save'"
                      />
                      <v-btn
                        id="btn-collaborators-cancel"
                        aria-label="Cancel Collaborator Edit"
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
                    v-if="!recordingTypeEditing && recordingTypeEditable"
                    id="btn-recording-type-edit"
                    aria-label="Edit Recording Type"
                    class="mt-3"
                    @click="toggleRecordingTypeEditing"
                  >
                    Edit
                  </v-btn>
                </div>
                <div
                  v-if="recordingTypeEditing && recordingTypeEditable"
                  id="select-recording-type"
                  :aria-activedescendant="`radio-recording-type-${recordingType}`"
                  aria-labelledby="select-recording-type-label"
                  class="mb-4"
                  role="radiogroup"
                  tabindex="0"
                >
                  <div
                    v-for="(recordingTypeOption, index) in recordingTypeOptions"
                    :key="recordingTypeOption"
                    class="d-flex flex-nowrap py-1"
                  >
                    <input
                      :id="`radio-recording-type-${recordingTypeOption}`"
                      :checked="recordingTypeOption === recordingType ? 'checked' : false"
                      class="ml-1 mr-3"
                      :disabled="recordingTypeUpdating"
                      type="radio"
                      :value="recordingTypeOption"
                      @change="() => onRecordingTypeChange(recordingTypeOption, index)"
                    />
                    <label class="font-size-16 text-secondary" :for="`radio-recording-type-${recordingTypeOption}`">
                      {{ displayLabels[recordingTypeOption] }}
                    </label>
                  </div>
                </div>
                <div v-if="recordingTypeEditing && recordingTypeEditable">
                  <ProgressButton
                    id="btn-recording-type-save"
                    :action="updateRecordingTypeClicked"
                    aria-label="Save Recording Type"
                    :disabled="recordingTypeUpdating"
                    :in-progress="recordingTypeUpdating"
                    :text="recordingTypeUpdating ? 'Saving' : 'Save'"
                  />
                  <v-btn
                    id="btn-recording-type-cancel"
                    aria-label="Cancel Recording Type Edit"
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
                    aria-label="Edit Recording Placement"
                    class="mt-3"
                    @click="togglePublishTypeEditing"
                  >
                    Edit
                  </v-btn>
                </div>
                <v-card v-if="publishTypeEditing" class="my-4 bg-surface-light">
                  <v-container>
                    <div
                      id="select-publish-type"
                      :aria-activedescendant="`radio-publish-type-${publishType}`"
                      aria-labelledby="select-publish-type-label"
                      class="mb-4"
                      role="radiogroup"
                      tabindex="0"
                    >
                      <div
                        v-for="(publishTypeOption, index) in publishTypeOptions"
                        :key="publishTypeOption"
                        class="d-flex flex-nowrap py-1"
                      >
                        <input
                          :id="`radio-publish-type-${publishTypeOption}`"
                          :checked="publishTypeOption === publishType ? 'checked' : false"
                          class="ml-1 mr-3"
                          :disabled="publishTypeUpdating"
                          type="radio"
                          :value="publishTypeOption"
                          @change="() => onPublishTypeChange(publishTypeOption, index)"
                        />
                        <label class="font-size-16 text--secondary" :for="`radio-publish-type-${publishTypeOption}`">{{ displayLabels[publishTypeOption] }}</label>
                      </div>
                    </div>
                    <!-- v-container doesn't seem to work with aria-live; therefore the following is a div. -->
                    <div v-if="publishType && publishType.startsWith('kaltura_media_gallery')" aria-live="polite">
                      <v-row
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
                        v-if="!currentUser.isAdmin"
                        align="end"
                        justify="start"
                      >
                        <v-col cols="9">
                          <v-select
                            id="select-canvas-site"
                            v-model="pendingCanvasSite"
                            dense
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
                            aria-label="Add bCourses Site"
                            color="success"
                            :disabled="!pendingCanvasSite"
                            @click="addCanvasSiteConfirm"
                          >
                            Add
                          </v-btn>
                        </v-col>
                      </v-row>
                      <v-row
                        v-if="!currentUser.isAdmin"
                        align="end"
                        justify="start"
                      >
                        <v-col cols="12">
                          To link a bCourses site from a past term, please <a :href="`mailto:${config.emailCourseCaptureSupport}`" target="_blank">
                            contact Course Capture support<span class="sr-only"> (this email link opens a new tab)</span></a>.
                        </v-col>
                      </v-row>
                      <v-row
                        v-if="currentUser.isAdmin"
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
                            aria-label="Add Canvas Site"
                            color="success"
                            :disabled="!pendingCanvasSiteId || !/^\d+$/.test(pendingCanvasSiteId) || isCanvasSiteIdStaged(pendingCanvasSiteId)"
                            @click="addCanvasSiteById"
                          >
                            Add
                          </v-btn>
                        </v-col>
                      </v-row>
                      <v-row
                        align="center"
                        justify="start"
                      >
                        <v-col cols="12">
                          <div
                            v-for="(site, index) in publishCanvasSites"
                            :id="`canvas-site-${site.canvasSiteId}`"
                            :key="site.canvasSiteId"
                            class="my-2"
                          >
                            {{ site.name }} ({{ site.courseCode }})
                            <v-btn
                              :id="`btn-canvas-site-remove-${site.canvasSiteId}`"
                              :aria-label="`Remove ${site.name} (${site.courseCode})`"
                              :disabled="publishTypeUpdating"
                              small
                              @click="removeCanvasSite(site.canvasSiteId, index)"
                            >
                              Remove
                            </v-btn>
                          </div>
                        </v-col>
                      </v-row>
                    </div>
                    <v-row
                      align="center"
                      justify="start"
                    >
                      <v-col cols="12">
                        <div>
                          <ProgressButton
                            id="btn-publish-type-save"
                            :action="updatePublishTypeClicked"
                            aria-label="Save Recording Placement"
                            :disabled="publishTypeUpdating || (publishType && publishType.startsWith('kaltura_media_gallery') && !publishCanvasSites.length)"
                            :in-progress="publishTypeUpdating"
                            :text="publishTypeUpdating ? 'Saving' : 'Save'"
                          />
                          <v-btn
                            id="btn-publish-type-cancel"
                            aria-label="Cancel Recording Placement Edit"
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
            <v-row v-if="!currentUser.isAdmin && get(course, 'publishType', '') === 'kaltura_my_media'">
              <v-col cols="12">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li>
                    <a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013882" target="_blank">
                      How to Publish from My Media
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                  <li>
                    <a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013623" target="_blank">
                      How to Embed in bCourses using the Rich Content Editor
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                  <li>
                    <a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115" target="_blank">
                      How to Download the Second Stream of the Recording
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                  <li>
                    <a href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq" target="_blank">
                      Course Capture FAQ
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                </ul>
              </v-col>
            </v-row>
            <v-row v-if="!currentUser.isAdmin && get(course, 'publishType', '').startsWith('kaltura_media_gallery')">
              <v-col cols="12">
                Based on the selected Recording Placement, please review the following KB articles:
                <ul>
                  <li>
                    <a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014032" target="_blank">
                      How to Remove a Recording from the Media Gallery
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                  <li>
                    <a href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115" target="_blank">
                      How to Download the Second Stream of the Recording
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                  <li>
                    <a href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq" target="_blank">
                      Course Capture FAQ
                      <span class="sr-only"> (link opens new browser tab)</span>
                    </a>
                  </li>
                </ul>
              </v-col>
            </v-row>
            <v-row v-if="currentUser.isAdmin">
              <v-col cols="12">
                <ScheduledCourse :course="course"></ScheduledCourse>
              </v-col>
            </v-row>
          </v-container>
          <v-container v-if="isCurrentTerm && capability && hasValidMeetingTimes && !course.deletedAt && (course.hasOptedOut || !course.scheduled)" class="elevation-2 pa-6">
            <v-row>
              <v-col class="font-weight-bold mb-1">
                <span v-if="course.hasOptedOut && !course.scheduled" id="notice-opt-out" class="red--text">
                  {{ currentUser.isAdmin ? 'The' : 'Your' }} course is not scheduled for Course Capture because one or more instructors have opted out. To schedule recordings, please have all instructors remove their opt-out status.
                </span>
                <span v-if="course.hasOptedOut && course.scheduled" id="notice-opt-out-pending" class="red--text">
                  {{ currentUser.isAdmin ? 'The' : 'Your' }} course is scheduled for Course Capture, but will be unscheduled shortly because one or more instructors have opted out. To keep recordings scheduled, please have all instructors remove their opt-out status.
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
                  <v-icon color="red" :icon="mdiAlert"></v-icon>
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
                  <v-icon color="red" :icon="mdiAlert"></v-icon>
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
                  <v-icon color="red" :icon="mdiAlert"></v-icon>
                </div>
                <div id="course-not-current">
                  This course is not currently eligible for Course Capture.
                </div>
              </div>
            </v-row>
          </v-container>
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

<script setup>
import {find, get, filter, isEmpty, isEqual, sortBy, size} from 'lodash'
import {DateTime} from 'luxon'
import {mdiBookMultipleOutline, mdiAlert} from '@mdi/js'
import {ref, reactive, computed, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {alertScreenReader, putFocusNextTick, getCourseCodes, getTermName} from '@/lib/utils'
import CanvasCourseSite from '@/components/course/CanvasCourseSite'
import CourseHistory from '@/components/course/CourseHistory'
import CoursePageSidebar from '@/components/course/CoursePageSidebar'
import {getAuditoriums} from '@/api/room'
import {getCanvasSitesTeaching} from '@/api/user'
import PageTitle from '@/components/util/PageTitle'
import PersonLookup from '@/components/util/PersonLookup'
import ProgressButton from '@/components/util/ProgressButton'
import ScheduledCourse from '@/components/course/ScheduledCourse'
import {
  deleteCourseNote,
  getCourse, getCourseSite,
  updateCollaborators,
  updateCourseNote,
  updatePublishType,
  updateRecordingType
} from '@/api/course'
import {useContextStore} from '@/stores/context'

const {config, currentUser, loadingStart, loadingComplete} = useContextStore()

const addCollaboratorError = ref('')
const agreedToTerms = ref(false)
const auditoriums = ref([])
const capability = ref(null)
const collaborators = ref([])
const collaboratorsEditing = ref(false)
const collaboratorsUpdating = ref(false)
const course = ref({
  meetings: {
    eligible: [],
    ineligible: []
  },
  instructors: [],
  collaborators: [],
  canvasSites: [],
  updateHistory: []
})
const courseDisplayTitle = ref('')
const displayLabels = reactive({
  kaltura_media_gallery: 'Publish to the Media Gallery (all members of the bCourses site will have access)',
  kaltura_my_media: 'Place in My Media (I will decide if and how I want to share)',
  presenter_presentation_audio: 'Camera Without Operator',
  presenter_presentation_audio_with_operator: `Camera With Operator ($${config.courseCapturePremiumCost} fee)`
})
const hasValidMeetingTimes = ref(false)
const instructors = ref([])
const instructorProxies = ref([])
const isLoading = ref(true)
const location = ref('')
const noteBody = ref('')
const noteEditing = ref(false)
const noteUpdating = ref(false)
const pendingCanvasSite = ref(null)
const pendingCanvasSiteId = ref(null)
const publishCanvasSites = ref([])
const publishCanvasSiteOptions = ref([])
const publishType = ref('')
const publishTypeEditing = ref(false)
const publishTypeOptions = ref([])
const publishTypeUpdating = ref(false)
const recordingType = ref('')
const recordingTypeEditing = ref(false)
const recordingTypeOptions = ref([])
const recordingTypeUpdating = ref(false)

// Computed
// const disableSubmit = computed(() => !agreedToTerms.value || !publishType.value || !recordingType.value)
const isCurrentTerm = computed(() => course.value.termId === config.currentTermId)
const recordingTypeEditable = computed(() =>
  recordingTypeOptions.value.length > 1 &&
  (currentUser.isAdmin || course.value.recordingType !== 'presenter_presentation_audio_with_operator')
)
const updatesQueued = computed(() => !!course.value.updateHistory.find(u => u.status === 'queued'))

onMounted(() => {
  isLoading.value = true
  loadingStart()
  const {params} = useRoute()
  getCourse(params.termId, params.sectionId)
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
      collaborators.value = [...data.collaborators]
      noteBody.value = data.note
      publishType.value = data.publishType
      recordingType.value = data.recordingType
      publishCanvasSites.value = [...data.canvasSites]
      recordingTypeOptions.value = meeting.room ? Object.keys(meeting.room.recordingTypeOptions || {}) : []
      publishTypeOptions.value = Object.keys(config.publishTypeOptions).sort().reverse()
      getAuditoriums().then(aud => {
        auditoriums.value = aud
        if (!currentUser.isAdmin) {
          getCanvasSitesTeaching(currentUser.uid).then(sites => {
            publishCanvasSiteOptions.value = sites
            isLoading.value = false
            loadingComplete(courseDisplayTitle.value)
          })
        } else {
          isLoading.value = false
          loadingComplete(courseDisplayTitle.value)
        }
      })
    })
})

const addCollaboratorConfirm = (collaborator) => {
  if (collaborator) {
    const exists = collaborators.value.some(c => c.uid === collaborator.uid)
    if (exists) {
      addCollaboratorError.value = `${collaborator.firstName} ${collaborator.lastName} is already a collaborator.`
      alertScreenReader(addCollaboratorError.value)
    } else {
      addCollaboratorError.value = null
      collaborators.value.push(collaborator)
      alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} added as a collaborator.`)
    }
    putFocusNextTick('collaborator-lookup-input')
  }
}

const addCanvasSiteById = () => {
  if (pendingCanvasSiteId.value && !isCanvasSiteIdStaged(pendingCanvasSiteId)) {
    getCourseSite(pendingCanvasSiteId.value).then(data => {
      if (data) {
        publishCanvasSites.value.push(data)
        alertScreenReader(`${data.name} added.`)
        putFocusNextTick('input-canvas-site-id')
      }
    })
  }
  pendingCanvasSiteId.value = null
}

const addCanvasSiteConfirm = () => {
  if (pendingCanvasSite.value && !isCanvasSiteIdStaged(pendingCanvasSite.canvasSiteId)) {
    publishCanvasSites.push(pendingCanvasSite)
  }
  alertScreenReader(`${pendingCanvasSite.name} added.`)
  putFocusNextTick('select-canvas-site')
  pendingCanvasSite.value = null
}

const cancelNote = () => {
  noteBody.value = course.value.note
  noteEditing.value = false
  noteUpdating.value = false
  alertScreenReader('Note edit canceled.')
  putFocusNextTick('btn-edit-note')
}

const collaboratorLabel = (collaborator) => {
  let label = `${collaborator.firstName} ${collaborator.lastName}`
  if (collaborator.email) label += ` (${collaborator.email})`
  return `${label} (${collaborator.uid})`
}

const deleteNote = () => {
  noteUpdating.value = true
  deleteCourseNote(course.value.termId, course.value.sectionId)
    .then(() => {
      course.value.note = null
      noteBody.value = null
      noteUpdating.value = false
      alertScreenReader('Note deleted.')
      putFocusNextTick('btn-edit-note')
    })
}

const editNote = () => {
  noteEditing.value = true
  putFocusNextTick('note-body-edit')
}

const isCanvasSiteIdStaged = (siteId) => {
  return !!find(publishCanvasSites, {'canvasSiteId': parseInt(siteId, 10)})
}

const onPublishTypeChange = (option, idx) => {
  publishType.value = publishType.value === option ? publishTypeOptions.value[idx - 1] : option
}

const onRecordingTypeChange = (option, idx) => {
  recordingType.value = recordingType.value === option ? recordingTypeOptions.value[idx - 1] : option
}

const removeCanvasSite = (canvasSiteId, index) => {
  const nextFocusIndex = (index + 1 === size(publishCanvasSites)) ? index - 1 : index + 1
  const nextFocusSiteId = get(publishCanvasSites, `${nextFocusIndex}.canvasSiteId`)
  const canvasSite = find(publishCanvasSites, c => c.canvasSiteId === canvasSiteId)
  const canvasSiteName = canvasSite.name || ''
  publishCanvasSites.value = filter(publishCanvasSites, c => c.canvasSiteId !== canvasSiteId)
  alertScreenReader(`Removed bCourses site ${canvasSiteName}.`)
  let nextFocusId = `btn-canvas-site-remove-${nextFocusSiteId}`
  if (isEmpty(publishCanvasSites) || !nextFocusSiteId) {
    nextFocusId = currentUser.isAdmin ? 'input-canvas-site-id' : 'select-canvas-site'
  }
  putFocusNextTick(nextFocusId)
}

const removeCollaborator = (uid, index) => {
  const collaborator = collaborators.value.find(c => c.uid === uid)
  collaborators.value = collaborators.value.filter(c => c.uid !== uid)
  alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} removed.`)
  const nextId = collaborators.value[index]?.uid || null
  putFocusNextTick(nextId ? `btn-collaborator-remove-${nextId}` : 'collaborator-lookup-input')
}

const saveNote = () => {
  noteUpdating.value = true
  updateCourseNote(course.value.termId, course.value.sectionId, noteBody.value)
    .then(data => {
      course.value.note = data.note
      noteBody.value = data.note
      noteEditing.value = false
      noteUpdating.value = false
      alertScreenReader('Note updated.')
      putFocusNextTick('btn-edit-note')
    })
}

const toggleCollaboratorsEditing = () => {
  collaboratorsEditing.value = true
  putFocusNextTick('collaborator-lookup-input')
}

const togglePublishTypeEditing = () => {
  publishTypeEditing.value = true
  putFocusNextTick('select-publish-type')
}

const toggleRecordingTypeEditing = () => {
  recordingTypeEditing.value = true
  putFocusNextTick('select-recording-type')
}

const updateCollaboratorsClicked = () => {
  collaboratorsUpdating.value = true
  updateCollaborators(
    collaborators.value.map(c => c.uid),
    course.value.sectionId,
    course.value.termId
  ).then(data => {
    alertScreenReader('Collaborators updated.')
    putFocusNextTick('btn-collaborators-edit')
    course.value.collaborators = data.collaborators
    collaboratorsEditing.value = false
    collaboratorsUpdating.value = false
    addCollaboratorError.value = null
  })
}

const updateCollaboratorsCancel = () => {
  alertScreenReader('Collaborator edit cancelled.')
  putFocusNextTick('btn-collaborators-edit')
  collaboratorsEditing.value = false
  collaboratorsUpdating.value = false
  addCollaboratorError.value = null
  collaborators.value = [...course.value.collaborators]
}

const updatePublishTypeClicked = () => {
  publishTypeUpdating.value = true
  updatePublishType(
    publishCanvasSites.value.map(s => s.canvasSiteId),
    publishType.value,
    course.value.sectionId,
    course.value.termId
  ).then(data => {
    const message = `Recording placement updated to ${data.publishTypeName}.`
    alertScreenReader(message)
    putFocusNextTick('btn-publish-type-edit')
    course.value.canvasSiteIds = data.canvasSiteIds
    course.value.canvasSites = data.canvasSites
    course.value.publishType = data.publishType
    course.value.publishTypeName = data.publishTypeName
    publishTypeEditing.value = false
    publishTypeUpdating.value = false
  })
}

const updatePublishTypeCancel = () => {
  alertScreenReader('Recording placement edit cancelled.')
  putFocusNextTick('btn-publish-type-edit')
  publishTypeEditing.value = false
  publishType.value = course.value.publishType
  publishCanvasSites.value = [...course.value.canvasSites]
}

const updateRecordingTypeClicked = () => {
  recordingTypeUpdating.value = true
  updateRecordingType(
    recordingType.value,
    course.value.sectionId,
    course.value.termId
  ).then(data => {
    const message = `Recording type updated to ${displayLabels[recordingType.value]}.`
    alertScreenReader(message)
    putFocusNextTick('btn-recording-type-edit')
    course.value.recordingType = data.recordingType
    course.value.recordingTypeName = data.recordingTypeName
    recordingTypeEditing.value = false
    recordingTypeUpdating.value = false
  })
}

const updateRecordingTypeCancel = () => {
  alertScreenReader('Recording type edit cancelled.')
  putFocusNextTick('btn-recording-type-edit')
  recordingTypeEditing.value = false
  recordingType.value = course.value.recordingType
}
</script>
