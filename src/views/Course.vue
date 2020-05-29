<template>
  <div v-if="!loading">
    <v-container fluid>
      <v-row class="pl-3">
        <h1>{{ course.label }}</h1>
      </v-row>
      <v-row class="pl-3">
        Section ID: {{ course.sectionId }}
      </v-row>
      <v-row class="pl-3">
        <h2 id="course-title">{{ course.courseTitle }}</h2>
      </v-row>
      <v-row>
        <v-col lg="3" md="3" sm="3">
          <CoursePageSidebar :after-unschedule="render" :course="course" />
        </v-col>
        <v-col>
          <v-card class="pa-6" outlined>
            <v-container v-if="course.room.capability">
              <v-row v-if="course.approvals.length" no-gutters>
                <v-col>
                  Approved by {{ oxfordJoin(approvedByNames) }}.
                </v-col>
              </v-row>
              <v-row v-if="course.scheduled">
                <v-col>
                  <ScheduledCourse :after-approve="render" :course="course" />
                </v-col>
              </v-row>
              <v-row no-gutters class="mb-4">
                <v-col>
                  <CourseCaptureExplained />
                  <div class="font-italic font-weight-light pl-2 pt-4">
                    <div v-if="course.room.isAuditorium">
                      <v-icon class="pr-1">mdi-information-outline</v-icon>
                      <strong>Note:</strong> 'Presentation and Audio' recordings are free.
                      There will be a &#36;{{ $config.courseCapturePremiumCost }} operator fee, per semester, for
                      'Presenter' recordings in {{ oxfordJoin($_.map(auditoriums, 'location')) }}.
                    </div>
                    <div :class="{'pt-2': course.room.isAuditorium}">
                      <v-icon v-if="!course.room.isAuditorium">mdi-information-outline</v-icon>
                      Choosing 'Media Gallery' will auto-publish recordings to students in bCourses.
                      Choosing 'My Media' will allow instructors to review/edit prior to publishing to students.
                    </div>
                  </div>
                </v-col>
              </v-row>
              <v-row v-if="!course.scheduled" justify="start" align="center">
                <v-col md="3" class="mb-6">
                  <h4>
                    <label id="select-recording-type-label" for="select-recording-type">Recording Type</label>
                  </h4>
                </v-col>
                <v-col md="6">
                  <div v-if="course.hasNecessaryApprovals" class="mb-5">
                    {{ mostRecentApproval.recordingTypeName }}
                  </div>
                  <div v-if="!course.hasNecessaryApprovals">
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
                      >
                        <span :id="`menu-option-recording-type-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item.text }}</span>
                      </v-select>
                    </div>
                  </div>
                </v-col>
              </v-row>
              <v-row
                v-if="!course.scheduled"
                align="center"
                justify="start"
                no-gutters
              >
                <v-col md="3" class="mb-6">
                  <h4>
                    <label id="select-publish-type-label" for="select-publish-type">Publish</label>
                  </h4>
                </v-col>
                <v-col md="6">
                  <div v-if="course.hasNecessaryApprovals" id="approved-publish-type" class="mb-5">
                    {{ mostRecentApproval.publishTypeName }}
                  </div>
                  <v-select
                    v-if="!course.hasNecessaryApprovals"
                    id="select-publish-type"
                    v-model="publishType"
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
              <v-row v-if="!course.hasNecessaryApprovals && !$currentUser.isAdmin" no-gutters align="start">
                <v-col md="auto">
                  <v-checkbox id="agree-to-terms-checkbox" v-model="agreedToTerms" class="mt-0"></v-checkbox>
                </v-col>
                <v-col>
                  <TermsAgreementText class="pt-1" />
                </v-col>
              </v-row>
              <v-row v-if="!course.hasNecessaryApprovals" lg="2">
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
            <v-container v-if="!course.room.capability">
              <v-row>
                <v-icon class="pr-2" color="red">mdi-alert</v-icon>
                This course is not eligible for Course Capture because {{ course.room.location }} is not capture-enabled.
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
  import CourseCaptureExplained from '@/components/util/CourseCaptureExplained'
  import CoursePageSidebar from '@/components/course/CoursePageSidebar'
  import ScheduledCourse from '@/components/course/ScheduledCourse'
  import TermsAgreementText from '@/components/util/TermsAgreementText'
  import Utils from '@/mixins/Utils'
  import {approve, getCourse} from '@/api/course'
  import {getAuditoriums} from '@/api/room'

  export default {
    name: 'Course',
    components: {CourseCaptureExplained, CoursePageSidebar, ScheduledCourse, TermsAgreementText},
    mixins: [Context, Utils],
    data: () => ({
      agreedToTerms: false,
      approvedByNames: undefined,
      auditoriums: undefined,
      course: undefined,
      isApproving: false,
      publishType: undefined,
      publishTypeOptions: undefined,
      recordingType: undefined,
      recordingTypeOptions: undefined
    }),
    computed: {
      disableSubmit() {
        return !this.agreedToTerms || !this.publishType || !this.recordingType
      },
      mostRecentApproval() {
        return this.$_.last(this.course.approvals)
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
      }).catch(this.$ready)
    },
    methods: {
      approve() {
        this.isApproving = true
        approve(this.publishType, this.recordingType, this.course.sectionId).then(data => {
          this.render(data)
          this.isApproving = false
        }).catch(this.$ready)
      },
      render(data) {
        this.$loading()
        this.agreedToTerms = this.$currentUser.isAdmin
        this.approvedByNames = []
        this.course = data
        this.recordingTypeOptions = []
        this.$_.each(this.course.room.recordingTypeOptions, (text, value) => {
          this.recordingTypeOptions.push({text, value})
        })
        if (this.course.approvals.length) {
          const mostRecent = this.$_.last(this.course.approvals)
          this.publishType = mostRecent.publishType
          this.recordingType = mostRecent.recordingType
          this.$_.each(this.course.approvals, approval => {
            const name = approval.approvedBy.uid === this.$currentUser.uid ? 'you' : approval.approvedBy.name
            this.approvedByNames.push(name + (approval.wasApprovedByAdmin ? ' (Course Capture admin)' : ''))
          })
        } else {
          if (this.recordingTypeOptions.length === 1) {
            this.recordingType = this.recordingTypeOptions[0].value
          }
        }
        this.setPageTitle(this.course.label)
        this.$ready()
      }
    }
  }
</script>
