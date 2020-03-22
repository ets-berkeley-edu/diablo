<template>
  <div v-if="!loading">
    <v-container fluid>
      <v-row class="pl-3">
        <h2>{{ pageTitle }}</h2>
      </v-row>
      <v-row class="pl-3">
        <h3>{{ section.courseTitle }}</h3>
      </v-row>
      <v-row>
        <v-col lg="3" md="3" sm="3">
          <v-card class="mb-3 mr-3 mt-3 pa-6" outlined tile>
            <v-row>
              <v-col md="auto">
                <v-icon>mdi-school-outline</v-icon>
              </v-col>
              <v-col>
                <span v-if="$currentUser.isAdmin">
                  <span v-for="instructor in section.instructors" :key="instructor.uid">
                    <router-link :id="`instructor-${instructor.uid}`" :to="`/user/${instructor.uid}`">{{ instructor.name }}</router-link>
                    <span v-if="!$_.last(instructor) && section.instructors.length > 1">and</span>
                  </span>
                </span>
                <span v-if="!$currentUser.isAdmin">
                  {{ oxfordJoin($_.map(section.instructors, 'name')) }}
                </span>
              </v-col>
            </v-row>
            <v-row v-if="section.meetingDays">
              <v-col md="auto">
                <v-icon>mdi-calendar</v-icon>
              </v-col>
              <v-col>
                {{ $_.join(section.meetingDays, ', ') }}
              </v-col>
            </v-row>
            <v-row v-if="section.meetingStartTime">
              <v-col md="auto">
                <v-icon>mdi-clock-outline</v-icon>
              </v-col>
              <v-col>
                {{ section.meetingStartTime }} - {{ section.meetingEndTime }}
              </v-col>
            </v-row>
            <v-row>
              <v-col md="auto">
                <v-icon>mdi-map-marker</v-icon>
              </v-col>
              <v-col v-if="section.room.id && $currentUser.isAdmin">
                {{ section.room.location }}
              </v-col>
              <v-col v-if="!section.room.id || !$currentUser.isAdmin">
                {{ section.room.location }}
              </v-col>
            </v-row>
          </v-card>
        </v-col>
        <v-col lg="9" md="9" sm="9">
          <v-card
            class="ma-3 pa-6"
            outlined
            tile
          >
            <v-container fluid>
              <v-row class="pb-4">
                <div>
                  <h4>Course Capture Sign-up</h4>
                  <div v-if="approvedByUids.length" class="font-weight-bold pb-2 pt-2 pink--text">
                    <span v-if="mostRecentApproval.approvedByUid === $currentUser.uid">
                      You submitted the preferences below.
                    </span>
                    <div v-if="mostRecentApproval.approvedByUid !== $currentUser.uid">
                      The preferences below were submitted by {{ getInstructorNames(approvedByUids) }}.
                    </div>
                    <div v-if="scheduled" class="pt-2">Recordings have been scheduled in Kaltura.</div>
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
                </div>
              </v-row>
              <v-row align="center">
                <v-col cols="4" class="mb-5">
                  <h5>
                    <label for="select-recording-type">Recording Type</label>
                    <v-tooltip bottom>
                      <template v-slot:activator="{ on }">
                        <v-icon
                          color="primary"
                          class="pb-1 pl-1"
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
                <v-col cols="8">
                  <div v-if="hasNecessaryApprovals" class="pb-5">
                    {{ mostRecentApproval.recordingTypeName }}
                  </div>
                  <div v-if="!hasNecessaryApprovals">
                    <div v-if="section.room.captureOptions.length === 1">
                      {{ section.room.captureOptions[0].text }}
                      <input type="hidden" name="recordingType" :value="section.room.captureOptions[0].value">
                    </div>
                    <div v-if="section.room.captureOptions.length > 1">
                      <v-select
                        id="select-recording-type"
                        v-model="recordingType"
                        :full-width="true"
                        :items="section.room.captureOptions"
                        label="Select..."
                        solo
                      ></v-select>
                    </div>
                  </div>
                </v-col>
              </v-row>
              <v-row align="center">
                <v-col cols="4" class="mb-5">
                  <h5>
                    <label for="select-publish-type">Publish</label>
                    <v-tooltip bottom>
                      <template v-slot:activator="{ on }">
                        <v-icon
                          color="primary"
                          class="pb-1 pl-1"
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
                <v-col cols="8">
                  <div v-if="hasNecessaryApprovals" class="pb-5">
                    {{ mostRecentApproval.publishTypeName }}
                  </div>
                  <v-select
                    v-if="!hasNecessaryApprovals"
                    id="select-publish-type"
                    v-model="publishType"
                    :full-width="true"
                    :items="publishTypeOptions"
                    label="Select..."
                    solo
                  ></v-select>
                </v-col>
              </v-row>
              <v-row v-if="!hasNecessaryApprovals">
                <v-col md="auto" class="mr-0 pr-0">
                  <v-checkbox id="agree-to-terms-checkbox" v-model="agreedToTerms" class="mt-0 mr-0 pt-1"></v-checkbox>
                </v-col>
                <v-col>
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
                </v-col>
              </v-row>
              <v-row v-if="!hasNecessaryApprovals" class="pr-5">
                <v-spacer />
                <v-btn color="success" :disabled="disableSubmit" @click="approveRecording">Approve</v-btn>
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
  import {approve, getApprovals} from '@/api/approval'

  export default {
    name: 'Approve',
    mixins: [Context, Utils],
    data: () => ({
      agreedToTerms: false,
      approvals: undefined,
      approvedByUids: undefined,
      hasNecessaryApprovals: undefined,
      instructorUids: undefined,
      mostRecentApproval: undefined,
      pageTitle: undefined,
      publishType: undefined,
      publishTypeOptions: undefined,
      recordingType: undefined,
      scheduled: undefined,
      section: undefined
    }),
    computed: {
      disableSubmit() {
        return !this.agreedToTerms || !this.publishType || !this.recordingType
      }
    },
    created() {
      const termId = this.$_.get(this.$route, 'params.termId')
      const sectionId = this.$_.get(this.$route, 'params.sectionId')
      getApprovals(termId, sectionId).then(data => {
        this.render(data)
        this.$ready()
      })
    },
    methods: {
      approveRecording() {
        approve(this.publishType, this.recordingType, this.section.sectionId).then(data => {
          this.render(data)
        })
      },
      getInstructorNames(uids) {
        const instructors = this.$_.filter(this.section.instructors, instructor => this.$_.includes(uids, instructor.uid))
        const unrecognized = this.$_.difference(uids, this.$_.map(this.section.instructors, 'uid'))
        const names = this.$_.union(this.$_.map(instructors, 'name'), unrecognized)
        return names.length ? this.oxfordJoin(names) : ''
      },
      render(data) {
        if (data.approvals.length) {
          this.approvals = this.$_.sortBy(data.approvals, ['createdAt'])
          this.approvedByUids = this.$_.map(this.approvals, 'approvedByUid')
          this.mostRecentApproval = this.$_.last(this.approvals)
          this.publishType = this.mostRecentApproval.publishType
          this.recordingType = this.mostRecentApproval.recordingType
        } else {
          this.approvals = []
          this.approvedByUids = []
        }
        this.hasNecessaryApprovals = data.hasNecessaryApprovals
        this.instructorUids = this.$_.map(data.section.instructors, 'uid')
        this.pageTitle = `${data.section.courseName } - ${data.section.instructionFormat} ${data.section.sectionNum}`
        this.publishTypeOptions = data.publishTypeOptions
        this.scheduled = data.scheduled
        this.section = data.section
        if (this.section.room.captureOptions.length === 1) {
          this.recordingType = this.section.room.captureOptions[0].value
        }
        this.setPageTitle(this.pageTitle)
        this.$ready()
      }
    }
  }
</script>
