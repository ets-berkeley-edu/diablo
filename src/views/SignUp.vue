<template>
  <div>
    <v-container fluid>
      <v-row class="pl-3">
        <h1>{{ pageTitle }}</h1>
      </v-row>
      <v-row class="pl-3">
        <h2>{{ section.courseTitle }}</h2>
      </v-row>
      <v-row>
        <v-col lg="3" md="3" sm="3">
          <v-card class="mb-3 mr-3 mt-3 pa-6" outlined tile>
            <v-row>
              <v-col md="auto">
                <v-icon>mdi-school-outline</v-icon>
              </v-col>
              <v-col>
                {{ oxfordJoin($_.map(section.instructors, 'name')) }}
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
              <v-col>
                {{ section.meetingLocation }}
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
            <v-row>
              <div>
                <h3>Course Capture Sign-up</h3>
                The Course Capture program is the campus service for recording and publishing classroom activity. If you
                sign up using this form, recordings of every class session will be automatically recorded. (For details,
                please read
                <a
                  id="link-to-course-capture-overview"
                  :href="$config.courseCaptureExplainedUrl"
                  target="_blank"
                  aria-label="Open URL to Course Capture service overview in a new window">Course Capture Services Explained <v-icon>mdi-open-in-new</v-icon></a>.
              </div>
            </v-row>
            <v-row>
              {{ section }}
            </v-row>
            <v-row>
              <v-col md="auto" class="mr-0 pr-0">
                <v-checkbox id="agree-to-terms-checkbox" v-model="agreedToTerms" class="mt-0 mr-0 pt-1"></v-checkbox>
              </v-col>
              <v-col>
                <label for="agree-to-terms-checkbox">
                  I have read the Audio and Video Recording Permission Agreement and I agree to the terms stated within.
                  (<a
                    id="link-to-course-capture-policies"
                    :href="$config.courseCapturePoliciesUrl"
                    target="_blank"
                    aria-label="Open URL to Course Capture policies in a new window">
                    Audio and Video Recording Permission Agreement <v-icon>mdi-open-in-new</v-icon>
                  </a>)
                </label>
              </v-col>
            </v-row>
            <v-row class="pr-5">
              <v-spacer />
              <v-btn color="success" :disabled="!agreedToTerms">Approve</v-btn>
            </v-row>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
  import Utils from '@/mixins/Utils'

  export default {
    name: 'SignUp',
    mixins: [Utils],
    data: () => ({
      agreedToTerms: false,
      section: undefined,
      pageTitle: undefined
    }),
    created() {
      const termId = this.$_.get(this.$route, 'params.termId')
      const sectionId = this.$_.get(this.$route, 'params.sectionId')
      this.section = this.$_.find(this.$currentUser.teachingSections, s => s['sectionId'] === sectionId && s['termId'] === termId)
      this.pageTitle = `${this.section.courseName } ${this.section.sectionNum} - ${this.section.instructionFormat} ${this.section.sectionNum}`
      this.setPageTitle(this.pageTitle)
    }
  }
</script>
