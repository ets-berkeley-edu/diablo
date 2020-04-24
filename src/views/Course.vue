<template>
  <div v-if="!loading" class="pa-3">
    <v-container fluid>
      <v-row class="pl-3">
        <h2 id="page-title">{{ pageTitle }}</h2>
      </v-row>
      <v-row class="pl-3">
        Section ID: {{ course.sectionId }}
      </v-row>
      <v-row class="pl-3">
        <h3 id="course-title">{{ course.courseTitle }}</h3>
      </v-row>
      <v-row>
        <v-col lg="3" md="3" sm="3">
          <v-card class="pa-6" outlined tile>
            <v-row id="instructors">
              <v-col md="auto">
                <v-icon>mdi-school-outline</v-icon>
              </v-col>
              <v-col>
                <span v-if="$currentUser.isAdmin">
                  <span v-for="(instructor, index) in course.instructors" :key="instructor.uid">
                    <router-link :id="`instructor-${instructor.uid}`" :to="`/user/${instructor.uid}`">{{ instructor.name }}</router-link>
                    <span v-if="course.instructors.length > 1 && index === course.instructors.length - 2"> and </span>
                  </span>
                </span>
                <span v-if="!$currentUser.isAdmin">
                  {{ oxfordJoin($_.map(course.instructors, 'name')) }}
                </span>
              </v-col>
            </v-row>
            <v-row v-if="course.meetingDays" id="meeting-days">
              <v-col md="auto">
                <v-icon>mdi-calendar</v-icon>
              </v-col>
              <v-col>
                {{ $_.join(course.meetingDays, ', ') }}
              </v-col>
            </v-row>
            <v-row v-if="course.meetingStartTime" id="meeting-times">
              <v-col md="auto">
                <v-icon>mdi-clock-outline</v-icon>
              </v-col>
              <v-col>
                {{ course.meetingStartTime }} - {{ course.meetingEndTime }}
              </v-col>
            </v-row>
            <v-row id="rooms">
              <v-col md="auto">
                <v-icon>mdi-map-marker</v-icon>
              </v-col>
              <v-col v-if="room.id && $currentUser.isAdmin">
                <router-link id="room" :to="`/room/${room.id}`">{{ room.location }}</router-link>
              </v-col>
              <v-col v-if="!room.id || !$currentUser.isAdmin">
                {{ room.location }}
              </v-col>
            </v-row>
            <v-row v-if="course.crossListings.length" id="cross-listings">
              <v-col md="auto">
                <v-icon>mdi-arrow-top-right-bottom-left-bold</v-icon>
              </v-col>
              <v-col>
                <h5>Cross-listings</h5>
                <span v-for="crossListing in course.crossListings" :key="crossListing.sectionId">
                  {{ crossListing.sectionId }}
                </span>
              </v-col>
            </v-row>
            <v-row v-if="course.canvasCourseSites.length" id="canvas-course-sites">
              <v-col md="auto">
                <v-icon>mdi-bookmark-outline</v-icon>
              </v-col>
              <v-col>
                <span v-for="canvasCourseSite in course.canvasCourseSites" :key="canvasCourseSite.courseSiteId">
                  <a
                    :id="`canvas-course-site-${canvasCourseSite.courseSiteId}`"
                    :href="`${$config.canvasBaseUrl}/courses/${canvasCourseSite.courseSiteId}`"
                    target="_blank">{{ canvasCourseSite.courseSiteName }}</a>
                  <span v-if="course.canvasCourseSites.length > 1 && index === course.canvasCourseSites.length - 2"> and </span>
                </span>
              </v-col>
            </v-row>
          </v-card>
        </v-col>
        <v-col>
          <v-card class="pa-6" outlined>
            <v-container>
              <v-row v-if="scheduled">
                <v-col>
                  <v-card tile>
                    <v-list-item-title class="pl-4 pt-4">
                      <h5 class="title">Recordings scheduled</h5>
                    </v-list-item-title>
                    <v-list-item two-line class="pb-3">
                      <v-list-item-content>
                        <v-list-item-title>Scheduled on</v-list-item-title>
                        <v-list-item-subtitle>{{ scheduled.createdAt | moment('MMM DD, YYYY') }}</v-list-item-subtitle>
                      </v-list-item-content>
                      <v-list-item-content>
                        <v-list-item-title>Recording Type</v-list-item-title>
                        <v-list-item-subtitle>{{ scheduled.recordingTypeName }}</v-list-item-subtitle>
                      </v-list-item-content>
                      <v-list-item-content>
                        <v-list-item-title>Publish Type</v-list-item-title>
                        <v-list-item-subtitle>{{ scheduled.publishTypeName }}</v-list-item-subtitle>
                      </v-list-item-content>
                    </v-list-item>
                  </v-card>
                </v-col>
              </v-row>
              <v-row no-gutters class="mb-6">
                <v-col>
                  <div v-if="!scheduled && approvedByUids.length" class="font-weight-bold pb-5 pink--text">
                    <span v-if="mostRecentApproval.approvedByUid === $currentUser.uid">
                      You submitted the preferences below.
                    </span>
                    <div v-if="mostRecentApproval.approvedByUid !== $currentUser.uid">
                      {{ getInstructorNames(approvedByUids) }} approved.
                    </div>
                  </div>
                  <div>
                    The Course Capture program is the campus service for recording and publishing classroom activity. If you
                    sign up using this form, recordings of every class session will be automatically recorded. (For details,
                    please read
                    <a
                      id="link-to-course-capture-overview"
                      :href="$config.courseCaptureExplainedUrl"
                      target="_blank"
                      aria-label="Open URL to Course Capture service overview in a new window">
                      Course Capture Services Explained <v-icon>mdi-open-in-new</v-icon>
                    </a>.
                  </div>
                </v-col>
              </v-row>
              <v-row v-if="!scheduled" justify="start" align="center">
                <v-col md="3" class="mb-6">
                  <h5>
                    <label for="select-recording-type">Recording Type</label>
                    <v-tooltip id="tooltip-recording-type" bottom>
                      <template v-slot:activator="{ on }">
                        <v-icon
                          color="primary"
                          class="pl-1"
                          dark
                          v-on="on">
                          mdi-information-outline
                        </v-icon>
                      </template>
                      <div>
                        Foo
                      </div>
                    </v-tooltip>
                  </h5>
                </v-col>
                <v-col md="6">
                  <div v-if="hasNecessaryApprovals" class="mb-5">
                    {{ mostRecentApproval.recordingTypeName }}
                  </div>
                  <div v-if="!hasNecessaryApprovals">
                    <div v-if="recordingTypeOptions.length === 1" class="mb-5">
                      {{ recordingTypeOptions[0].text }}
                      <input type="hidden" name="recordingType" :value="recordingTypeOptions[0].value">
                    </div>
                    <div v-if="recordingTypeOptions.length > 1">
                      <v-select
                        id="select-recording-type"
                        v-model="recordingType"
                        item-text="text"
                        item-value="value"
                        :full-width="true"
                        :items="recordingTypeOptions"
                        label="Select..."
                        solo
                      ></v-select>
                    </div>
                  </div>
                </v-col>
              </v-row>
              <v-row v-if="!scheduled" justify="start" align="center">
                <v-col md="3" class="mb-6">
                  <h5>
                    <label for="select-publish-type">Publish</label>
                    <v-tooltip id="tooltip-publish" bottom>
                      <template v-slot:activator="{ on }">
                        <v-icon
                          color="primary"
                          class="pl-1"
                          dark
                          v-on="on">
                          mdi-information-outline
                        </v-icon>
                      </template>
                      <div>
                        You can publish into bCourses, under Media Gallery [link to KB article: Media Gallery] Publish
                        under all instructors' My Media. Instructor will need to publish to Media Gallery on their own
                        (link to KB article: publishing from my media)
                      </div>
                    </v-tooltip>
                  </h5>
                </v-col>
                <v-col md="6">
                  <div v-if="hasNecessaryApprovals" id="approved-publish-type" class="mb-5">
                    {{ mostRecentApproval.publishTypeName }}
                  </div>
                  <v-select
                    v-if="!hasNecessaryApprovals"
                    id="select-publish-type"
                    v-model="publishType"
                    item-text="text"
                    item-value="value"
                    :items="publishTypeOptions"
                    label="Select..."
                    solo
                  ></v-select>
                </v-col>
              </v-row>
              <v-row v-if="!hasNecessaryApprovals" no-gutters align="start">
                <v-col md="auto">
                  <v-checkbox id="agree-to-terms-checkbox" v-model="agreedToTerms" class="mt-0"></v-checkbox>
                </v-col>
                <v-col>
                  <div class="pt-1">
                    <label for="agree-to-terms-checkbox">
                      I have read the Audio and Video Recording Permission Agreement and I agree to the terms stated within.
                      <a
                        id="link-to-course-capture-policies"
                        :href="$config.courseCapturePoliciesUrl"
                        target="_blank"
                        aria-label="Open URL to Course Capture policies in a new window">
                        Audio and Video Recording Permission Agreement <v-icon>mdi-open-in-new</v-icon>
                      </a>.
                    </label>
                  </div>
                </v-col>
              </v-row>
              <v-row v-if="!hasNecessaryApprovals" lg="2">
                <v-spacer />
                <v-col md="2">
                  <v-btn
                    id="btn-approve"
                    color="success"
                    :disabled="disableSubmit"
                    @click="approveRecording">
                    Approve
                  </v-btn>
                </v-col>
              </v-row>
            </v-container>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {approve, getApprovals} from '@/api/course'

  export default {
    name: 'Course',
    mixins: [Context, Utils],
    data: () => ({
      agreedToTerms: false,
      approvals: undefined,
      approvedByUids: undefined,
      course: undefined,
      hasNecessaryApprovals: undefined,
      mostRecentApproval: undefined,
      pageTitle: undefined,
      publishType: undefined,
      publishTypeOptions: undefined,
      recordingType: undefined,
      recordingTypeOptions: undefined,
      room: undefined,
      scheduled: undefined
    }),
    computed: {
      disableSubmit() {
        return !this.agreedToTerms || !this.publishType || !this.recordingType
      }
    },
    created() {
      this.$loading()
      const termId = this.$_.get(this.$route, 'params.termId')
      const sectionId = this.$_.get(this.$route, 'params.sectionId')
      getApprovals(termId, sectionId).then(data => {
        this.render(data)
        this.publishTypeOptions = []
        this.$_.each(this.$config.publishTypeOptions, (text, value) => {
          this.publishTypeOptions.push({text, value})
        })
      }).catch(this.$ready)
    },
    methods: {
      approveRecording() {
        approve(this.publishType, this.recordingType, this.course.sectionId).then(data => {
          this.render(data)
        }).catch(this.$ready)
      },
      getInstructorNames(uids) {
        const instructors = this.course.instructors
        const filtered = this.$_.filter(instructors, instructor => this.$_.includes(uids, instructor.uid))
        const unrecognized = this.$_.difference(uids, this.$_.map(filtered, 'uid'))
        const names = this.$_.union(this.$_.map(filtered, 'name'), unrecognized)
        return names.length ? this.oxfordJoin(names) : ''
      },
      render(data) {
        this.$loading()
        this.room = data.room
        this.recordingTypeOptions = []
        this.$_.each(this.room.recordingTypeOptions, (text, value) => {
          this.recordingTypeOptions.push({text, value})
        })
        if (data.approvals.length) {
          this.approvals = this.$_.sortBy(data.approvals, ['createdAt'])
          this.approvedByUids = this.$_.map(this.approvals, 'approvedByUid')
          this.mostRecentApproval = this.$_.last(this.approvals)
          this.publishType = this.mostRecentApproval.publishType
          this.recordingType = this.mostRecentApproval.recordingType
        } else {
          this.approvals = []
          this.approvedByUids = []
          if (this.recordingTypeOptions.length === 1) {
            this.recordingType = this.recordingTypeOptions[0].value
          }
        }
        this.hasNecessaryApprovals = data.hasNecessaryApprovals
        this.pageTitle = data.label
        this.scheduled = data.scheduled
        this.course = data
        this.setPageTitle(this.pageTitle)
        this.$ready()
      }
    }
  }
</script>